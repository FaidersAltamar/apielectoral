import os
from scrapper.procuraduria_scraper import ProcuraduriaScraperAuto


def test_no_saved_html_when_no_name():
    html = '<div class="datosConsultado">Señor(a)</div>'
    scraper = ProcuraduriaScraperAuto()
    result = scraper.extract_result_data(html)
    # result should be dict and not include a saved HTML path; nombre_completo must be None
    assert result is not None
    assert result.get('nombre_completo') is None
    assert 'failed_html' not in result

