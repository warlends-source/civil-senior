"""Construtor de .docx a partir de um memorial oficial da empresa usado como TEMPLATE.

Preserva do template: cabecalho (logo, bloco de titulo, pagina n/N, codigo, revisao), estilos
(FirstParagraph, Corpodetexto, Compact, Titulo1-3, Sumario1-3), numeracao, tema e configuracoes.
Substitui apenas o corpo. Elementos reproduzidos fielmente do documento oficial:
  - tabela estilo 'Table', bordas cinza 808080, cabecalho D9E2F3, paragrafos 'Compact' (20/20)
  - equacao numerada: paragrafo Corpodetexto com tabs (centro 4465 / direita 8931) + <m:oMath> + (n)
  - titulos manuais numerados ("1. INTRODUCAO") nos estilos Titulo1/2/3
O sumario e um campo TOC; atualizar_campos() usa o Word (COM) para preenche-lo e paginar.
"""
import re
import shutil
import zipfile
from xml.sax.saxutils import escape as _e

import calc_ast as ca

W_TEXTO = 8921            # largura util em dxa (como no template)


def esc(t):
    return _e(t)


def run(t, b=False, i=False, sz=None, cor=None, sup=False, sub=False):
    rp = ""
    if b:
        rp += "<w:b/><w:bCs/>"
    if i:
        rp += "<w:i/><w:iCs/>"
    if cor:
        rp += '<w:color w:val="%s"/>' % cor
    if sz:
        rp += '<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (sz, sz)
    if sup:
        rp += '<w:vertAlign w:val="superscript"/>'
    if sub:
        rp += '<w:vertAlign w:val="subscript"/>'
    return '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % ("<w:rPr>%s</w:rPr>" % rp if rp else "", esc(t))


STORE_ID = "{6B0B5E2A-7C3D-4F57-9E11-4D1A5C2B8F10}"
NS_MEM = "urn:civil-senior:memorial"
_SDT_IDS = {"CodigoDocumento": 710001, "RevisaoDocumento": 710002}
_sdt_seq = [720000]


def sdt(tag, alias, texto, rpr=""):
    """Controle de conteudo (texto simples) VINCULADO ao XML interno /memorial/<campo>.
    Editar um controle atualiza todos os outros (cabecalho e tabela) com o mesmo vinculo."""
    campo = {"CodigoDocumento": "codigo", "RevisaoDocumento": "revisao"}[tag]
    _sdt_seq[0] += 1
    return ('<w:sdt><w:sdtPr>' + rpr + '<w:alias w:val="%s"/><w:tag w:val="%s"/><w:id w:val="%d"/>'
            "<w:dataBinding w:prefixMappings=\"xmlns:m='%s'\" w:xpath=\"/m:memorial[1]/m:%s[1]\" w:storeItemID=\"%s\"/>"
            '<w:text/></w:sdtPr><w:sdtContent><w:r>%s<w:t>%s</w:t></w:r></w:sdtContent></w:sdt>'
            % (esc(alias), tag, _sdt_seq[0], NS_MEM, campo, STORE_ID, rpr, esc(texto)))


def _inline(conteudo, **kw):
    """conteudo: str | ('m', omml) | ('b', texto) | ('i', texto) | lista desses."""
    if isinstance(conteudo, (str, tuple)):
        conteudo = [conteudo]
    out = []
    for c in conteudo:
        if isinstance(c, str):
            out.append(run(c, **kw))
        elif c[0] == "m":
            out.append("<m:oMath>%s</m:oMath>" % c[1])
        elif c[0] == "b":
            out.append(run(c[1], b=True, **{k: v for k, v in kw.items() if k != "b"}))
        elif c[0] == "i":
            out.append(run(c[1], i=True, **{k: v for k, v in kw.items() if k != "i"}))
        elif c[0] == "sup":
            out.append(run(c[1], sup=True))
        elif c[0] == "sdt":
            out.append(sdt(c[1], c[2], c[3]))
    return "".join(out)


def p(conteudo, estilo="Corpodetexto", jc=None, antes=None, depois=None, keep_next=False, **kw):
    ppr = '<w:pStyle w:val="%s"/>' % estilo
    if keep_next:
        ppr += "<w:keepNext/>"
    if antes is not None or depois is not None:
        ppr += '<w:spacing%s%s/>' % (' w:before="%d"' % antes if antes is not None else "",
                                      ' w:after="%d"' % depois if depois is not None else "")
    if jc:
        ppr += '<w:jc w:val="%s"/>' % jc
    return "<w:p><w:pPr>%s</w:pPr>%s</w:p>" % (ppr, _inline(conteudo, **kw))


def titulo_doc(l1, l2, l3):
    return (p(l1, "FirstParagraph", jc="center", depois=120, b=True, sz=28) +
            p(l2, jc="center", depois=120, b=True, sz=24) +
            p(l3, jc="center", depois=120, b=True, sz=24))


def h(nivel, texto):
    return '<w:p><w:pPr><w:pStyle w:val="Ttulo%d"/></w:pPr>%s</w:p>' % (nivel, run(texto))


def eq(omml_xml, numero=None, extra_antes=80, extra_depois=80):
    tabs = '<w:tabs><w:tab w:val="center" w:pos="4465"/><w:tab w:val="right" w:pos="8931"/></w:tabs>'
    num = ("<w:r><w:tab/></w:r>" + run("(%d)" % numero)) if numero else ""
    return ('<w:p><w:pPr><w:pStyle w:val="Corpodetexto"/>%s<w:keepLines/><w:spacing w:before="%d" w:after="%d"/></w:pPr>'
            '<w:r><w:tab/></w:r><m:oMath>%s</m:oMath>%s</w:p>' % (tabs, extra_antes, extra_depois, omml_xml, num))


def _cel(conteudo, w, fill=None, jc=None, bold=False):
    shd = '<w:shd w:val="clear" w:color="auto" w:fill="%s"/>' % fill if fill else ""
    ppr = '<w:pStyle w:val="Compact"/><w:spacing w:before="20" w:after="20"/>' + ('<w:jc w:val="%s"/>' % jc if jc else "")
    return ('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/>%s<w:vAlign w:val="center"/></w:tcPr>'
            '<w:p><w:pPr>%s</w:pPr>%s</w:p></w:tc>' % (w, shd, ppr, _inline(conteudo, b=bold) if bold else _inline(conteudo)))


def tabela(cabecalhos, linhas, larguras, alinh=None, destaque_ultima_col=False):
    """larguras em fracao (soma 1). alinh: lista 'left'/'center'/'right' por coluna."""
    tot = W_TEXTO
    ws = [int(tot * x) for x in larguras]
    ws[-1] += tot - sum(ws)
    alinh = alinh or ["left"] * len(ws)
    borda = "".join('<w:%s w:val="single" w:sz="4" w:space="0" w:color="808080"/>' % s
                    for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
    x = ('<w:tbl><w:tblPr><w:tblStyle w:val="Table"/><w:tblW w:w="5000" w:type="pct"/>'
         '<w:tblBorders>%s</w:tblBorders><w:tblLayout w:type="fixed"/>'
         '<w:tblLook w:val="0020" w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="0"/>'
         '</w:tblPr><w:tblGrid>%s</w:tblGrid>' % (borda, "".join('<w:gridCol w:w="%d"/>' % w for w in ws)))
    x += '<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>%s</w:tr>' % "".join(
        _cel(c, w, fill="D9E2F3", jc="center" if a != "left" else None, bold=True) for c, w, a in zip(cabecalhos, ws, alinh))
    for ln in linhas:
        x += '<w:tr><w:trPr><w:cantSplit/></w:trPr>%s</w:tr>' % "".join(
            _cel(c, w, jc=(a if a != "left" else None)) for c, w, a in zip(ln, ws, alinh))
    return x + "</w:tbl>" + p("", "Compact", depois=60)


def toc():
    fld = ('<w:p><w:pPr><w:pStyle w:val="Corpodetexto"/></w:pPr>'
           '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
           '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-3" \\h \\z \\u </w:instrText></w:r>'
           '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
           '<w:r><w:t>Atualize o sumário (clique com o botão direito &gt; Atualizar campo).</w:t></w:r>'
           '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')
    return fld


def quebra_pagina():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


_fig_seq = [0]


def figura(rid, largura_cm, proporcao_h_w, nome, descr, legenda):
    """Figura centralizada (imagem inline) + legenda, nos estilos CaptionedFigure e ImageCaption do template.
    rid: id da relacao (ver montar(imagens=...)); proporcao_h_w = altura/largura da imagem."""
    _fig_seq[0] += 1
    cx = int(largura_cm * 360000)
    cy = int(cx * proporcao_h_w)
    draw = ('<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="%d" cy="%d"/>'
            '<wp:docPr id="%d" name="%s" descr="%s"/><wp:cNvGraphicFramePr>'
            '<a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/>'
            '</wp:cNvGraphicFramePr><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr>'
            '<pic:cNvPr id="%d" name="%s"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="%s"/>'
            '<a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/>'
            '<a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
            '</a:graphicData></a:graphic></wp:inline></w:drawing>'
            % (cx, cy, 9000 + _fig_seq[0], esc(nome), esc(descr), 9000 + _fig_seq[0], esc(nome), rid, cx, cy))
    par_img = ('<w:p><w:pPr><w:pStyle w:val="CaptionedFigure"/><w:keepNext/><w:jc w:val="center"/></w:pPr>'
               '<w:r>%s</w:r></w:p>' % draw)
    par_leg = ('<w:p><w:pPr><w:pStyle w:val="ImageCaption"/><w:jc w:val="center"/></w:pPr>%s</w:p>' % run(legenda))
    return par_img + par_leg


def _custom_xml(codigo, revisao):
    cab = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    item = (cab + '<memorial xmlns="%s"><codigo>%s</codigo>'
            '<revisao>%s</revisao></memorial>' % (NS_MEM, esc(codigo), esc(revisao)))
    props = (cab +
             '<ds:datastoreItem ds:itemID="%s" xmlns:ds="http://schemas.openxmlformats.org/officeDocument/2006/customXml">'
             '<ds:schemaRefs><ds:schemaRef ds:uri="%s"/></ds:schemaRefs></ds:datastoreItem>' % (STORE_ID, NS_MEM))
    rels = (cab +
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXmlProps" '
            'Target="itemProps1.xml"/></Relationships>')
    return item, props, rels


def _vincular_cabecalho(x, codigo, revisao):
    """Troca 'A DEFINIR' e o valor de REV. do cabecalho por controles vinculados."""
    x = re.sub(r'<w:r>(<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>)<w:t>A DEFINIR</w:t></w:r>',
               lambda m: sdt("CodigoDocumento", "Código do documento", codigo, m.group(1)), x, count=1)
    x = re.sub(r'(REV\.</w:t></w:r><w:r><w:br/></w:r>)<w:r>(<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>)<w:t>[^<]*</w:t></w:r>',
               lambda m: m.group(1) + sdt("RevisaoDocumento", "Revisão", revisao, m.group(2)), x, count=1)
    return x


def montar(template, saida, corpo_xml, titulo_meta=None, codigo="A DEFINIR", revisao="0", imagens=None):
    """Copia o template e troca apenas o corpo do document.xml (preserva cabecalho/estilos/sectPr).
    imagens: {rid: caminho_png} - copiadas para word/media e ligadas ao documento (ver figura())."""
    imagens = imagens or {}
    zin = zipfile.ZipFile(template)
    doc = zin.read("word/document.xml").decode("utf8")
    ini = doc.index("<w:body>") + len("<w:body>")
    sect = re.findall(r"<w:sectPr.*?</w:sectPr>", doc, re.S)[-1]
    novo = doc[:ini] + corpo_xml + sect + "</w:body></w:document>"
    usados = set(re.findall(r'r:(?:embed|id)="([^"]+)"', novo))        # relacoes ainda usadas pelo novo corpo
    zout = zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED)
    rels_doc = zin.read("word/_rels/document.xml.rels").decode("utf8")
    hdr_rels = (zin.read("word/_rels/header1.xml.rels").decode("utf8")
                if "word/_rels/header1.xml.rels" in zin.namelist() else "")
    item_xml, props_xml, item_rels = _custom_xml(codigo, revisao)
    for it in zin.infolist():
        data = zin.read(it.filename)
        if re.match(r"word/header\d+\.xml$", it.filename) and "A DEFINIR" in data.decode("utf8"):
            data = _vincular_cabecalho(data.decode("utf8"), codigo, revisao).encode("utf8")
        elif it.filename == "[Content_Types].xml":
            s = data.decode("utf8")
            s = s.replace("</Types>", '<Override PartName="/customXml/itemProps1.xml" ContentType='
                          '"application/vnd.openxmlformats-officedocument.customXmlProperties+xml"/></Types>')
            data = s.encode("utf8")
        if it.filename == "word/document.xml":
            data = novo.encode("utf8")
        elif it.filename.startswith("word/media/"):
            # imagens do corpo antigo nao sao mais referenciadas; as do cabecalho continuam via header1.xml.rels
            if it.filename.split("/")[-1] not in hdr_rels:
                continue
        elif it.filename == "word/_rels/document.xml.rels":
            # remove relacoes de imagem do corpo antigo (evita referencias a arquivos descartados)
            data = re.sub(r'<Relationship [^>]*Target="media/[^"]+"[^>]*/>', "", rels_doc)
            extra = "".join('<Relationship Id="%s" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                            'Target="media/fig_%s.png"/>' % (rid, rid) for rid in imagens)
            data = data.replace("</Relationships>", '<Relationship Id="rIdMemorial1" Type='
                                '"http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXml" '
                                'Target="../customXml/item1.xml"/>' + extra + '</Relationships>').encode("utf8")
        elif it.filename == "docProps/core.xml" and titulo_meta:
            s = data.decode("utf8")
            s = re.sub(r"<dc:title>.*?</dc:title>", "<dc:title>%s</dc:title>" % esc(titulo_meta), s)
            data = s.encode("utf8")
        zout.writestr(it.filename, data)
    for rid, caminho in imagens.items():
        with open(caminho, "rb") as f_img:
            zout.writestr("word/media/fig_%s.png" % rid, f_img.read())
    zout.writestr("customXml/item1.xml", item_xml)
    zout.writestr("customXml/itemProps1.xml", props_xml)
    zout.writestr("customXml/_rels/item1.xml.rels", item_rels)
    zout.close()


def atualizar_campos(docx, pdf=None):
    """Abre no Word (invisivel), atualiza sumario/campos/paginacao, salva e exporta PDF."""
    import win32com.client as w
    import os
    word = w.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        d = word.Documents.Open(os.path.abspath(docx), False, False)
        d.Repaginate()
        for toc_ in d.TablesOfContents:
            toc_.Update()
        d.Fields.Update()
        for sec in d.Sections:
            for hf in sec.Headers:
                hf.Range.Fields.Update()
        d.Repaginate()
        paginas = d.ComputeStatistics(2)
        d.Save()
        if pdf:
            d.ExportAsFixedFormat(os.path.abspath(pdf), 17)
        d.Close(False)
        return paginas
    finally:
        word.Quit()


def definir_codigo(docx, codigo=None, revisao=None, pdf=None):
    """Atualiza o codigo/revisao do documento (cabecalho + tabela) via Word e regera o PDF.
    Uso: python -c "import docx_template as d; d.definir_codigo('arquivo.docx', 'XXX-000-CIV-MCA-0001', '0', 'arquivo.pdf')" """
    import os
    import win32com.client as w
    word = w.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        d = word.Documents.Open(os.path.abspath(docx), False, False)
        parts = d.CustomXMLParts.SelectByNamespace(NS_MEM)
        if parts.Count == 0:
            raise RuntimeError("documento sem o XML interno do memorial (gere-o com docx_template.montar)")
        part = parts.Item(1)
        part.NamespaceManager.AddNamespace("m", NS_MEM)
        for campo, valor in (("codigo", codigo), ("revisao", revisao)):
            if valor is not None:
                part.SelectSingleNode("/m:memorial/m:%s" % campo).Text = str(valor)
        for sec in d.Sections:
            for hf in sec.Headers:
                hf.Range.Fields.Update()
        d.Repaginate()
        for toc_ in d.TablesOfContents:
            toc_.Update()
        d.Save()
        if pdf:
            d.ExportAsFixedFormat(os.path.abspath(pdf), 17)
        d.Close(False)
    finally:
        word.Quit()
