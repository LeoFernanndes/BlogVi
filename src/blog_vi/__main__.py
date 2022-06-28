import sys
from pathlib import Path

from blog_vi._config import SETTINGS_FILENAME
from blog_vi._settings import Settings, get_settings
from blog_vi.core.article import Article
from blog_vi.core.landing import Landing
from blog_vi.core.translations.engine import TranslateEngine
from blog_vi.core.translations.exceptions import (
    ProviderSettingsNotFound, TranslateEngineNotFound, BadProviderSettingsError
)
from blog_vi.core.utils import get_articles_from_csv, prepare_workdir


def generate_blog(workdir: Path) -> None:
    workdir, templates_dir = prepare_workdir(workdir)

    settings_dict = get_settings(workdir / SETTINGS_FILENAME)
    settings = Settings(workdir, templates_dir, **settings_dict)

    url = settings.blog_post_location_url
    articles = get_articles_from_csv(url)

    index = Landing.from_settings(settings)

    for cnt, article in enumerate(articles):
        if article['Status'] != '1':
            continue

        article['Title'] = article.get('Title') or f'blog-{cnt}'

        if article['Legacy Slugs'] != '':
            article['Is Legacy'] = False
            article_obj = Article.from_config(settings, index, article)
            redirect_slug = article_obj.slug
            index.add_article(article_obj)
            legacy_slugs = article['Legacy Slugs'].split(';')
            for slug in legacy_slugs:
                article['Slug'] = slug
                article['Is Legacy'] = True
                article['Redirect Slug'] = redirect_slug
                print(article)
                print()
                article_obj = Article.from_config(settings, index, article)
                index.add_article(article_obj)

        else:
            article['Is Legacy'] = False
            article_obj = Article.from_config(settings, index, article)
            index.add_article(article_obj)
            print(article_obj.__dict__['slug'])
            print()

    index.generate()

    if settings.translate_articles:
        try:
            if settings.source_language is None:
                print('[-] Please, provide a source language abbreviation.')
                sys.exit(1)
            engine = TranslateEngine(index, settings.source_language['abbreviation'])
        except ProviderSettingsNotFound:
            print(f'[-] Settings not found for translate provider {settings.translator}')
        except TranslateEngineNotFound:
            print('[-] Translate engine not found')
        except BadProviderSettingsError:
            print(f'[-] Please, fill all {settings.translator} provider settings')
        except TypeError:
            print('[-] Please define translator provider in settings')
        else:
            engine.translate()

    index.cache_changes()
