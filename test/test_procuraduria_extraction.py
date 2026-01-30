from scrapper.procuraduria_scraper import ProcuraduriaScraperAuto


def test_extract_name_from_spans():
    html = '<div class="datosConsultado"><span>JUAN</span><span>PABLO</span><span>PEREZ</span><span>GOMEZ</span></div>'
    scraper = ProcuraduriaScraperAuto()
    result = scraper.extract_result_data(html)
    assert result is not None
    assert result.get("nombre_completo") == "JUAN PABLO PEREZ GOMEZ"


def test_extract_name_from_label():
    html = '<div class="datosConsultado"><p><strong>Nombre:</strong> Maria Fernanda Lopez Perez</p></div>'
    scraper = ProcuraduriaScraperAuto()
    result = scraper.extract_result_data(html)
    assert result is not None
    assert "Maria Fernanda Lopez Perez" in result.get("nombre_completo")


def test_extract_name_from_table():
    html = '<div class="datosConsultado"><table><tr><td>Nombre</td><td>Carlos Alberto Ruiz</td></tr></table></div>'
    scraper = ProcuraduriaScraperAuto()
    result = scraper.extract_result_data(html)
    assert result is not None
    assert "Carlos Alberto Ruiz" in result.get("nombre_completo")
