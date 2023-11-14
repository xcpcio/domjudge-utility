import pdfplumber, colorama, pandas as pd, argparse, os
from colorama import Fore, Back, Style
colorama.init(autoreset=True)

def load_pdf(path, find_table = True):
    pdf = pdfplumber.open(path)
    print(pdf.metadata)
    print('Total Pages: ', len(pdf.pages))
    if not find_table:
        return pdf
    tables = []
    for i, page in enumerate(pdf.pages):
        tb_found = page.find_tables()
        if len(tb_found) > 0:
            tables.append(i)
            print('Page Index', i, 'Has ', len(tb_found), ' Table.')
    return pdf, tables

def extract_table(pdf, pages):
    merged_tb = []
    for page in pages:
        tb = pdf.pages[page].extract_table(
            table_settings={"horizontal_strategy": "lines"})
        if tb is None:
            continue

        #remove '\n'
        for row in tb:
            for i, cell in enumerate(row):
                row[i] = cell.replace('\n', '')
        merged_tb = merged_tb + tb
    return merged_tb

def save_to_xlsx(table, path):
    table_data = pd.DataFrame(table[1:], columns = table[0])
    table_data.to_excel(path, index = False)

def save_to_csv(table, path):
    table_data = pd.DataFrame(table[1:], columns = table[0])
    table_data.to_csv(path, index = False)

#parse index strings, e.g. 1-5,7,9-10
def index_parser(input):
    pages = []
    for index in input.split(','):
        if '-' in index:
            start, end = index.split('-')
            for i in range(int(start), int(end) + 1):
                pages.append(i)
        else:
            pages.append(int(index))
    return pages

#find longest continues sublist from a list
def find_longest_continues_index(input):
    longest_continues_index = []
    continues_index = []
    i = 0
    while i < len(input):
        if len(continues_index) == 0:
            continues_index.append(input[i])
        elif input[i] - continues_index[-1] == 1:
            continues_index.append(input[i])
        else:
            if len(continues_index) > len(longest_continues_index):
                longest_continues_index = continues_index
            continues_index = [input[i]]
        i = i + 1
    if len(continues_index) > len(longest_continues_index):
        longest_continues_index = continues_index
    return longest_continues_index

#parse arguments
parser = argparse.ArgumentParser(usage='%(prog)s pdf_file [options]', description='Extract table from pdf file.')
parser.add_argument('file', type=str, help='pdf path')
parser.add_argument('--output',  type=str, default='./output/', help='output directory, default is ./output/')

supported_output_formats = ['xlsx', 'csv', 'ALL']
parser.add_argument('--format',  type=str, default = 'xlsx', choices=supported_output_formats, help='output format, default is xlsx')
parser.add_argument('--auto', action='store_true', default = False, help='auto select longest continues pages with tables to parse')
parser.add_argument('--pages',  type=str, help='specify pages range to parse, e.g. 1-5,7,9-10')
args = parser.parse_args()

if args.file == '':
    print(Fore.RED + 'ERROR' + Fore.RESET + ' Please specify the pdf by --file.')
    exit(0)

if os.path.exists(args.file) == False:
    print(Fore.RED + 'ERROR' + Fore.RESET + ' File not found: ' + os.path.abspath(args.file))
    exit(0)

if os.path.exists(args.output) == False:
    print(Fore.GREEN + 'INFO' + Fore.RESET + ' Output directory not exsited, create it: ' + os.path.abspath(args.output))
    os.mkdir(args.output)

print(Fore.GREEN + 'INFO' + Fore.RESET + ' Start to extract table from ' + os.path.abspath(args.file))

path = args.file
output_home = args.output
if output_home[-1] != '/':
    output_home = output_home + '/'

pdf, tables = load_pdf(path)

#find longest continues pages from tables

longest_continues_pages = find_longest_continues_index(tables)
print('Longest Continues Pages With Tables: ', longest_continues_pages)
if args.auto:
    print(Fore.GREEN + 'INFO' + Fore.RESET + ' Auto select longest continues pages with tables to parse.')
    pages = longest_continues_pages
elif args.pages is None:
    print(Fore.WHITE + Back.RED + 'WARNNING' + Fore.RESET + Back.RESET + ' Run again with ' + Back.GREEN + '--pages' + Back.RESET + ' to specify pages to parse, or use ' + Back.GREEN + '--auto' + Back.RESET + ' to auto select longest continues pages with tables to parse.')
    exit(0)
else:
    pages = index_parser(args.pages)


print(Fore.GREEN + 'INFO' + Fore.RESET + ' Parsing Pages: ', pages)
data = extract_table(pdf, pages)
print(Fore.GREEN + 'INFO' + Fore.RESET + ' Parsed Tables With' + Back.GREEN, len(data), Back.RESET + 'Rows.')

output_formats = []
if args.format == 'ALL':
    output_formats = supported_output_formats[:-1]
else:
    output_formats.append(args.format)

name = os.path.basename(path)
name = os.path.splitext(name)[0]
for format in output_formats:
    output_path = output_home + name + '.' + format
    print(Fore.GREEN + 'INFO' + Fore.RESET + ' Saving to ' + output_path)
    if format == 'xlsx':
        save_to_xlsx(data, output_path)
    elif format == 'csv':
        save_to_csv(data, output_path)
    else:
        print(Fore.RED + 'ERROR' + Fore.RESET + ' Unsupported format: ' + format)
        exit(0)

print(Back.GREEN + Fore.WHITE + 'SUCCESS' + Style.RESET_ALL)
