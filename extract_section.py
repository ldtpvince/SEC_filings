from bs4 import BeautifulSoup
import re
import pandas as pd
from itertools import islice
import glob
import unicodedata

def read_section(lines, start_section, end_section, section_tag_with_matches):
    if len(section_tag_with_matches[start_section]) == 1:
        index = 0
    else:
        index = 1

    start_line, start_pos = section_tag_with_matches[start_section][index].sourceline - 1, section_tag_with_matches[start_section][index].sourcepos
    end_line, end_pos = section_tag_with_matches[end_section][index].sourceline - 1, section_tag_with_matches[end_section][index].sourcepos

    if end_line == start_line:
        section_content = lines[start_line][start_pos:end_pos]
    elif end_line == start_line + 1:
        section_content = lines[start_line][start_pos:] + lines[end_line][:end_pos] 
    elif end_line > start_line + 1:
        section_content = "".join(lines[start_line + 1:end_line])
        section_content = lines[start_line][start_pos:] + section_content + lines[end_line][:end_pos] 
    else:
        raise Exception("Wrong retrieved sections")

    section_soup = BeautifulSoup(section_content, "html.parser")
    return section_soup.get_text("")
    


def extract_section(file_path):
    with open(file_path, "r") as f:
        report_doc = f.read()

    soup = BeautifulSoup(report_doc, "html.parser")

    section_reg = {
        '1': re.compile(r'(?i)(^ITEM(\s|&#160;|&nbsp;)1(?![0-9a-zA-Z])([\w\W]*?BUSINESS|))'),
        '1A': re.compile(r'(?i)(^ITEM(\s|&#160;|&nbsp;)1A([\w\W]*?RISK\sFACTORS|))'),
        '1B': re.compile(r'(?i)(^ITEM(\s|&#160;|&nbsp;)1B([\w\W]*?UNRESOLVED\sSTAFF\sCOMMENTS|))'),
        '7': re.compile(r'(?i)(^ITEM(\s|&#160;|&nbsp;)7(?![A-Z])([\w\W]*?MANAGEMENT&#8217;S\sDISCUSSION\sAND\sANALYSIS\sOF\sFINANCIAL\sCONDITION\sAND\sRESULTS\sOF\sOPERATIONS|))'),
        '7A': re.compile(r'(?i)(^ITEM(\s|&#160;|&nbsp;)7A([\w\W]*?QUANTITATIVE\sAND\sQUALITATIVE\sDISCLOSURES\sABOUT\sMARKET\sRISK|))'),
    }

    tag_with_matches = {
        '1': [],
        '1A': [],
        '1B': [],
        '7': [],
        '7A': [],
    }

    for tag in soup.find_all():
        if tag.contents is not None:
            text = tag.find(text=True, recursive=False)

            if text is None:
                continue
            else:
                text = text.strip()

            for section in section_reg:
                match_section = section_reg[section].finditer(text)
                matches = [match for match in match_section]

                if len(matches) > 0:
                    tag_with_matches[section].append(tag)

    with open("test_reg.txt", "w") as f:
        f.write(str(tag_with_matches))

    lines = report_doc.splitlines()

    with open("test_reg_1.txt", "w") as f:
        section_content = read_section(lines, "1", "1A", tag_with_matches)
        f.write(section_content)

    with open("test_reg_1a.txt", "w") as f:
        section_content = read_section(lines, "1A", "1B", tag_with_matches)
        f.write(section_content)

    with open("test_reg_7.txt", "w") as f:
        section_content = read_section(lines, "7", "7A", tag_with_matches)
        f.write(section_content)

if __name__ == "__main__":
    extract_section("filings/0000793952-22-000014.txt")