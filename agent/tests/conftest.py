from pathlib import Path

import pytest
from pptx import Presentation
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
