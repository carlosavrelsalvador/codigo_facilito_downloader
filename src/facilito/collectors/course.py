from playwright.async_api import BrowserContext, Page

from ..constants import BASE_URL
from ..errors import CourseError, UnitError
from ..helpers import slugify
from ..models import Chapter, Course, Unit
from .helpers import get_unit_type


async def _fetch_course_chapters(page: Page) -> list[Chapter]:
    CHAPTERS_SELECTOR = (
        ".collapsible.no-box-shadow.no-border.f-topics.no-time div.f-top-16"
    )

    try:
        chapters_selectors = page.locator(CHAPTERS_SELECTOR)
        chapters_count = await chapters_selectors.count()

        if not chapters_count:
            raise CourseError()

        chapters: list[Chapter] = []
        for i in range(chapters_count):
            CHAPTER_NAME_SELECTOR = "header h4"
            UNITS_SELECTOR = ".collapsible-body ul a"
            UNIT_NAME_SELECTOR = ".box p.ibm"

            chapter_name = (
                await chapters_selectors.nth(i)
                .locator(CHAPTER_NAME_SELECTOR)
                .first.text_content()
            )

            units_locators = chapters_selectors.nth(i).locator(UNITS_SELECTOR)
            units_count = await units_locators.count()

            if not chapter_name or not units_count:
                raise CourseError()

            units: list[Unit] = []
            for j in range(units_count):
                unit_name = (
                    await units_locators.nth(j)
                    .locator(UNIT_NAME_SELECTOR)
                    .first.text_content()
                )

                unit_url = await units_locators.nth(j).first.get_attribute("href")

                if not unit_name or not unit_url:
                    raise CourseError()

                units.append(
                    Unit(
                        type=get_unit_type(unit_url),
                        name=unit_name,
                        slug=slugify(unit_name),
                        url=BASE_URL + unit_url,
                    )
                )

            chapters.append(
                Chapter(
                    name=chapter_name,
                    slug=slugify(chapter_name),
                    units=units,
                )
            )

    except Exception:
        raise UnitError()

    finally:
        await page.close()

    return chapters


async def fetch_course(context: BrowserContext, url: str) -> Course:
    NAME_SELECTOR = ".f-course-presentation h1"
    DESCRIPTION_SELECTOR = ".f-course-presentation div.f-top-small p"

    try:
        page = await context.new_page()
        await page.goto(url)

        name = await page.locator(NAME_SELECTOR).first.text_content()
        description = await page.locator(DESCRIPTION_SELECTOR).first.text_content()

        if not name or not description:
            raise CourseError()

        chapters = await _fetch_course_chapters(page)

    except Exception:
        raise CourseError()

    finally:
        await page.close()

    return Course(
        name=name,
        slug=slugify(name),
        url=url,
        chapters=chapters,
        description=description,
    )
