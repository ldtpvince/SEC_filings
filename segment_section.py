from bs4 import BeautifulSoup
import regex as re
import json

def text_preprocess_segment(text):
    def remove_whitespace(match):
        ws = r"[^\S\r\n]"
        return f"{match[1]}{re.sub(ws, r'', match[2])}{match[3]}{match[4]}"

    def remove_newline(match):
        newline = r"\n+"
        return rf"{match[0]}{re.sub(newline, r'', match[1])}{match[2]}"

    # normalize the text
    text = text.encode("ascii", "ignore").decode()

    # convert the text to lower
    text = text.lower()
 
    # clean multi-whitespace & multi-newline
    text = re.sub(r"[ ]+\n", "\n", text)
    text = re.sub(r"\n[ ]+", "\n", text)
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r" +", " ", text)
 
    text = re.sub(r"\n\.\n", ".\n", text)
    text = re.sub(r"\n\.", ".\n", text)

    # remove potential white space in "ITEM"
    text = re.sub(r"(?i)(\n[^\S\r\n]*)(I[^\S\r\n]*T[^\S\r\n]*E[^\S\r\n]*M)([^\S\r\n]+)(\d{1,2}[AB]?)",
                      remove_whitespace, text)
    
    # remove newline
    text = re.sub(r"(?i)(ITEM)(\n+)([0-9]\.{0,1})(\n+)", remove_newline, text)
    
    # remove url
    text = re.sub(r"\w+:\/\/\S+", r"", text)

    return text

def text_postprocess_segment(text):
    def remove_between_symbol(match):
        return rf"{match.group(1)} {match.group(2)}"

    # remove page number & number from table in general
    text = re.sub(r"\n[^\S\r\n]*[-‒–—]*\d+[-‒–—]*[^\S\r\n]*\n", r"\n", text, re.I|re.M|re.S)

    # remove all unecessary characters
    text = re.sub(r"([^a-z\s\.;,-])", "", text)

    # remove duplicate newline, dot, comma
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"\.+", ".", text)
    text = re.sub(r"\,+", ",", text)

    # fix text before & after comma in one paragraph
    text = re.sub(r"\s+,\s+", ", ", text)
    text = re.sub(r"\s+\.\n+", ".\n", text)

    # remove newline in-between sentence
    text = re.sub(r"([a-z])\n([a-z])", remove_between_symbol, text)

    # separate word that has - 
    text = re.sub(r"([a-z])\-([a-z])", remove_between_symbol, text)
    return text

# heuristic find the start and end of each section
def find_section_start_end(matches, anchor_item_list, start_item, end_item):
    longest_text = 0
    start, end = -1, -1

    if len(matches[end_item]) >= 2 and len(matches[start_item]) >= 2:
        if matches[end_item][0].start() < matches[start_item][0].start():
            start, end = matches[start_item][0].start(), matches[end_item][1].start()
        else:
            start, end = matches[start_item][1].start(), matches[end_item][1].start()

            if start > end:
                for i in range(len(matches[end_item])):
                    end = matches[end_item][i].start()

                    if end > start:
                        break

    elif len(matches[end_item]) == 1 and len(matches[start_item]) >=2:
        if matches[end_item][0].end() > matches[start_item][1].start():
            start, end = matches[start_item][1].start(), matches[end_item][0].start()
        else:
            subsitute_end_item = anchor_item_list[end_item]
            if subsitute_end_item == 'end':
                start, end = matches[start_item][1].start(), 0
            else:
                for item_section in matches[subsitute_end_item]:
                    if  item_section.end() > matches[start_item][1].start():
                        start, end = matches[start_item][1].start(),  item_section.start()
                        break

    elif len(matches[start_item]) == 1 and len(matches[end_item]) >=2:
        subsitute_start_item = None
        for item in anchor_item_list:
            if anchor_item_list[item] == start_item:
                subsitute_start_item = item

        for item_section in reversed(matches[subsitute_start_item]):
            if item_section.end() > matches[end_item][1].start():
                start, end = item_section.end(), matches[end_item][1].start()

    else:
        start, end = matches[start_item][0].start(), matches[end_item][0].start()

    if start < end:
        return start, end
    else:
        return -1, -1    

def segment_section(file_name):
    with open("filings/" + file_name, "r") as f:
        report_doc = f.read()

    document_start = re.search(r"(?i)\<DOCUMENT\>", report_doc)
    document_end = re.search(r"(?i)\<\/DOCUMENT\>", report_doc)
    content_10K = report_doc[document_start.start():document_end.end()]

    soup = BeautifulSoup(content_10K, "html.parser")
    xbrl_none_display_tag = soup.find("div", attrs={"style": re.compile(r"display:none\;{0,1}")})

    if xbrl_none_display_tag is not None:
        xbrl_none_display_tag.extract()
    
    raw_text = soup.get_text("\n")
    text = text_preprocess_segment(raw_text)

    re_flag = re.IGNORECASE | re.MULTILINE | re.BESTMATCH
    section_pattern = {
        '1': '^ITEM(\s|)1\.{0,1}([\n|\s]+BUSINESS)', 
        '1A': '^ITEM(\s|)1A\.{0,1}([\n|\s]+RISK\sFACTORS)', 
        '1B': '^ITEM(\s|)1B\.{0,1}([\n|\s]+UNRESOLVED\sSTAFF\sCOMMENTS)', 
        '2': '^ITEM(\s|)2\.{0,1}([\n|\s]+PROPERTIES)', 
        '3': '^ITEM(\s|)2\.{0,1}([\n|\s]+LEGAL\sPROCEEDINGS)', 
        '4': '^ITEM(\s|)2\.{0,1}([\n|\s]+MINE\sSAFETY\sDISCLOSURES)', 
        '5': '^ITEM(\s|)2\.{0,1}([\n|\s]+MARKET\sFOR\sREGISTRANT)', 
        '6': '^ITEM(\s|)2\.{0,1}([\n|\s]+CONSOLIDATED\sFINANCIAL\sDATA)', 
        # '7': '^ITEM(\s|)7\.{0,1}([\n|\s]+MANAGEMENT\'{0,1}S\sDISCUSSION\sAND\sANALYSIS\sOF\sFINANCIAL\sCONDITION\sAND\sRESULTS\sOF\sOPERATIONS)', 
        '7': '^ITEM(\s|)7\.{0,1}([\n|\s]+MANAGEMENT\'{0,1}S\sDISCUSSION\sAND\sANALYSIS\sOF\sFINANCIAL)', 
        '7A': '^ITEM(\s|)7A\.{0,1}([\n|\s]+QUANTITATIVE\sAND\sQUALITATIVE\sDISCLOSURES\sABOUT\sMARKET\sRISK)', 
        '8': '^ITEM(\s|)8\.{0,1}([\n|\s]+FINANCIAL\sSTATEMENTS)', 
        # '9': '^ITEM(\s|)9\.{0,1}([\n|\s]+CHANGES\sIN\sAND\sDISAGREEMENTS\sWITH\sACCOUNTANTS\sON\sACCOUNTING\sAND\sFINANCIAL\sDISCLOSURE)', 
        '9': '^ITEM(\s|)9\.{0,1}([\n|\s]+CHANGES\sIN\sAND\sDISAGREEMENTS\sWITH\sACCOUNTANTS\sON\sACCOUNTING)', 
        '9A': '^ITEM(\s|)9A\.{0,1}([\n|\s]+CONTROLS\sAND\sPROCEDURES)', 
        '9B': '^ITEM(\s|)9B\.{0,1}([\n|\s]+OTHER\sINFORMATION)',
        '9C': '^ITEM(\s|)9B\.{0,1}([\n|\s]+DISCLOSURE\sREGARDING\sFOREIGN\sJURISDICTIONS\sTHAT\sPREVENT\sINSPECTIONS)',
        '10': '^ITEM(\s|)10\.{0,1}([\n|\s]+DIRECTORS,\sEXECUTIVE\sOFFICERS\sAND\sCORPORATE\sGOVERNANCE)',
        '11': '^ITEM(\s|)11\.{0,1}([\n|\s]+EXECUTIVE\sCOMPENSATION)', 
        # '12': '^ITEM(\s|)12\.{0,1}([\n|\s]+SECURITY\sOWNERSHIP\sOF\sCERTAIN\sBENEFICIAL\sOWNERS\sAND\sMANAGEMENT\sAND\sRELATED\sSTOCKHOLDER\sMATTERS)',
        '12': '^ITEM(\s|)12\.{0,1}([\n|\s]+SECURITY\sOWNERSHIP\sOF\sCERTAIN\sBENEFICIAL)',
        # '13': '^ITEM(\s|)13\.{0,1}([\n|\s]+CERTAIN\sRELATIONSHIPS\sAND\sRELATED\sTRANSACTIONS,\sAND\sDIRECTOR\sINDEPENDENCE)', 
        '13': '^ITEM(\s|)13\.{0,1}([\n|\s]+CERTAIN\sRELATIONSHIPS\sAND\sRELATED)', 
        '14': '^ITEM(\s|)14\.{0,1}([\n|\s]+PRINCIPAL\sACCOUNTING\sFEES\sAND\sSERVICES)', 
        '15': '^ITEM(\s|)15\.{0,1}([\n|\s]+EXHIBITS\,{0,1}\sAND\sFINANCIAL\sSTATEMENT\sSCHEDULES)', 
        '16': '^ITEM(\s|)16\.{0,1}([\n|\s]+FORM\s10-K\sSUMMARY)',
    }

    match_candidates = {}
    missing_section = {}

    for section in section_pattern:
        len_pattern = len(section_pattern[section])
        fuzzy_match = rf"({section_pattern[section]}){{e<={5}}}"
        matches = [ match for match in re.finditer(fuzzy_match, text, re_flag)]

        if len(matches) == 0:
            missing_section[section] = 1
            continue

        for match in matches:
            if section in match_candidates:
                match_candidates[section].append(match)
            else:
                match_candidates[section] = [match]

    anchor_end_item_list = {
        '1': '1A',
        '1A': '1B',
        '1B': '2',
        '2': '3',
        '3': '4',
        '4': '5',
        '5': '6',
        '6': '7',
        '7': '7A',
        '7A': '8',
        '8': '9', 
        '9': '9A', 
        '9A': '9B', 
        '9B': '9C',
        '9C': '10',
        '10': '11', 
        '11': '12', 
        '12': '13', 
        '13': '14', 
        '14': '15',
        '15': '16',
        '16': 'end'
    }

    previous_section = None
    for section in anchor_end_item_list:
        if section in missing_section:
            anchor_end_item_list[previous_section] = anchor_end_item_list[section]
        else:
            previous_section = section

    for section in missing_section:
        anchor_end_item_list.pop(section, None)

    all_contents = {}

    for start_item in anchor_end_item_list:
        end_item = anchor_end_item_list[start_item]

        if end_item == "end":
            section_content = text[section_start:]
            continue

        section_start, section_end = find_section_start_end(match_candidates, anchor_end_item_list, start_item, end_item)

        if (section_start, section_end) == (-1, -1):
            section_content = None
        elif section_end == 0:
            section_content = text[section_start:]
        else:
            section_content = text[section_start:section_end]
            section_content = text_postprocess_segment(section_content)

        all_contents[start_item] = section_content

    for section in missing_section:
        all_contents[section] = None

    with open(f"sections/{file_name.split('.')[0]}.json", "w") as f:
        json.dump(all_contents, f, indent=2)