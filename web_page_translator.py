from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import requests

app = Flask(__name__)

PREDEFINED_APPS = {
    "Space News (space.com)": "https://www.space.com/",
    "Todo App": "https://www.todoist.com/",
    "Markdown Editor": "https://stackedit.io/",
    "Facebook" : "https://www.facebook.com/"
}

LANGUAGES = {
    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German', 'it': 'Italian',
    'pt': 'Portuguese', 'ja': 'Japanese', 'zh-cn': 'Chinese (Simplified)', 'hi': 'Hindi',
    'ta': 'Tamil', 'te': 'Telugu', 'bn': 'Bengali', 'gu': 'Gujarati', 'kn': 'Kannada',
    'ml': 'Malayalam', 'mr': 'Marathi', 'pa': 'Punjabi', 'or': 'Odia', 'as': 'Assamese'
}


def extract_text(html_content):
    """Extract visible text from HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup(['script', 'style']):
        tag.decompose()
    text_nodes = [
        element.strip() for element in soup.find_all(string=True)
        if element.strip() and element.parent.name not in ['script', 'style']
    ]
    return text_nodes, soup


def translate_text(text_nodes, target_language='es'):
    """Translate visible texts using GoogleTranslator."""
    translator = GoogleTranslator(source='auto', target=target_language)
    translated_texts = []
    for text in text_nodes:
        try:
            translated = translator.translate(text)
            translated_texts.append(translated if translated else text)
        except Exception as e:
            print(f"Translation error for '{text}': {e}")
            translated_texts.append(text) 
    return translated_texts


def replace_text_in_html(soup, original_texts, translated_texts):
    """Replace original visible texts with translations."""
    text_nodes = [
        el for el in soup.find_all(string=True)
        if el.strip() and el.parent.name not in ['script', 'style']
    ]
    for i, el in enumerate(text_nodes):
        if i < len(translated_texts) and el.strip() == original_texts[i]:
            if translated_texts[i] is not None:
                el.replace_with(translated_texts[i])
    return soup.body.decode_contents() if soup.body else ''


@app.route('/', methods=['GET', 'POST'])
def index():
    translated_html = None
    selected_language = 'en'
    url = ''
    error = ''

    if request.method == 'POST':
        selected_language = request.form.get('language', 'en')
        url = request.form.get('url', '').strip()
        predefined = request.form.get('predefined_app', '')

        if not url and predefined:
            url = predefined

        if url and not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        if url:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                originals, soup = extract_text(response.text)
                translated = translate_text(originals, selected_language)
                translated_html = replace_text_in_html(soup, originals, translated)

            except Exception as e:
                error = f"Could not fetch or translate: {e}"

    return render_template(
        'language.html',
        translated_html=translated_html,
        languages=LANGUAGES.items(),
        selected_language=selected_language,
        url=url,
        error=error,
        predefined_apps=PREDEFINED_APPS.items()
    )


if __name__ == '__main__':
    app.run(debug=True)
