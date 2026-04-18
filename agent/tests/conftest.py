from pathlib import Path

import pytest
from pptx import Presentation
from pptx.util import Inches
from sqlmodel import SQLModel, Session, create_engine

import app.db as db_module
from app.main import app


@pytest.fixture(autouse=True)
def isolated_test_db(tmp_path):
    db_file = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    original_engine = db_module.engine
    original_get_session = db_module.get_session

    db_module.engine = engine

    def get_session_override():
        with Session(engine) as session:
            yield session

    db_module.get_session = get_session_override
    app.dependency_overrides[original_get_session] = get_session_override

    try:
        yield
    finally:
        app.dependency_overrides.clear()
        db_module.engine = original_engine
        db_module.get_session = original_get_session


@pytest.fixture
def build_fixture_pptx(tmp_path):
    def _build(filename: str = "fixture.pptx", slides: list[str] | None = None) -> Path:
        presentation = Presentation()
        texts = slides or ["Editable rebuild"]
        for index, text in enumerate(texts):
            if index == 0:
                slide = presentation.slides.add_slide(presentation.slide_layouts[0])
                slide.shapes.title.text = text
                if len(slide.placeholders) > 1:
                    slide.placeholders[1].text = f"{text} body"
            else:
                slide = presentation.slides.add_slide(presentation.slide_layouts[1])
                slide.shapes.title.text = text
                slide.placeholders[1].text = f"{text} body"
        if presentation.slides:
            first_slide = presentation.slides[0]
            # Remove the blank starter slide inserted by the default template if still empty.
            if len(texts) > 0 and len(first_slide.shapes) == 0:
                pass
        output = tmp_path / filename
        presentation.save(output)
        return output

    return _build


@pytest.fixture
def build_fixture_pptx_with_picture(tmp_path):
    def _build(filename: str = "picture-fixture.pptx") -> Path:
        presentation = Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[5])
        slide.shapes.title.text = "Picture import"
        image_path = Path(__file__).resolve().parent / "fixtures" / "slides" / "slide-1.png"
        slide.shapes.add_picture(str(image_path), left=1_000_000, top=1_200_000, width=2_000_000, height=1_500_000)
        output = tmp_path / filename
        presentation.save(output)
        return output

    return _build


@pytest.fixture
def build_fixture_pptx_with_table(tmp_path):
    def _build(filename: str = "table-fixture.pptx") -> Path:
        presentation = Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[5])
        slide.shapes.title.text = "Table import"
        table_shape = slide.shapes.add_table(2, 2, Inches(1), Inches(1.6), Inches(4.5), Inches(1.6))
        table = table_shape.table
        table.cell(0, 0).text = "Metric"
        table.cell(0, 1).text = "Value"
        table.cell(1, 0).text = "Revenue"
        table.cell(1, 1).text = "22%"
        output = tmp_path / filename
        presentation.save(output)
        return output

    return _build


@pytest.fixture
def build_fixture_pptx_with_icon_card(tmp_path):
    def _build(filename: str = "icon-card-fixture.pptx") -> Path:
        presentation = Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[5])
        slide.shapes.title.text = "Icon card import"
        image_path = Path(__file__).resolve().parent / "fixtures" / "slides" / "slide-1.png"
        slide.shapes.add_picture(str(image_path), left=900000, top=1600000, width=700000, height=700000)

        title_box = slide.shapes.add_textbox(left=1800000, top=1550000, width=2200000, height=500000)
        title_box.text_frame.text = "Launch update"

        body_box = slide.shapes.add_textbox(left=1800000, top=2150000, width=3000000, height=800000)
        body_box.text_frame.text = "Pilot city opened in March."

        output = tmp_path / filename
        presentation.save(output)
        return output

    return _build
