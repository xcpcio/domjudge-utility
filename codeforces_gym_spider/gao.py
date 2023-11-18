import json, os, argparse, colorama, random, string, time, hashlib, requests, getpass
from inputimeout import inputimeout,TimeoutOccurred
from bs4 import BeautifulSoup as bs
from datetime import datetime
from colorama import Fore, Back, Style
colorama.init(autoreset=True)

extensions = (
            ('++', 'cpp'),
            ('GNU C', 'c'), 
            ('JavaScript', 'js'),
            ('Java', 'java'),
            ('Py', 'py'),
            ('Delphi', 'dpr'),
            ('FPC', 'pas'),
            ('C#', 'cs'),
            ('D', 'd'),
            ('Q#', 'qs'),
            ('Node', 'js'),
            ('Kotlin', 'kt'),
            ('Go', 'go'),
            ('Ruby', 'rb'),
            ('Rust', 'rs'),
            ('Perl', 'pl'),
            ('Scala', 'scala'),
            ('PascalABC', 'pas'),
            ('Haskell', 'hs'),
            ('PHP', 'php'))
def load_credential_json(path):
    with open(path, 'r') as f:
        result = json.load(f)
    return {'api_key': result['api_key'], 'api_secret':result['api_secret']}

def info(log):
    print(Style.RESET_ALL + Fore.GREEN + 'INFO ' + Fore.RESET + log)
def error(log):
    print(Style.RESET_ALL + Fore.RED + 'ERROR ' + Fore.RESET + log)
def warn(log):
    print(Style.RESET_ALL + Fore.YELLOW + 'WARN ' + Fore.RESET + log)

def issue_request(method, params, cred):
    key = cred['api_key']
    secret = cred['api_secret']
    letters = string.ascii_letters + string.digits
    rand = ''.join(random.choice(letters) for _ in range(6))
    now = int(time.time())
    sig_plain = '%s/%s?apiKey=%s&%s&time=%d#%s'%(rand, method, key, params, now, secret)
    #print(sig_plain)
    alg = hashlib.new("sha512", sig_plain.encode(encoding='ascii'))
    api_sig = alg.hexdigest()
    uri = 'https://codeforces.com/api/%s?%s&apiKey=%s&time=%d&apiSig=%s%s'%(method, params, key, now, rand, api_sig) 
    #print(uri)
    r = requests.get(uri)
    return r

def get_submissions(gym_id, cred):
    response = issue_request("contest.status", 'contestId=%d'%(gym_id), cred)
    if response.status_code != 200:
        error('STATUS API Failed: %d %s'%(response.status_code, response.text))
        exit(2)
    result = json.loads(response.text)
    if result['status'] != 'OK':
        error('STATUS API Failed: ' + result['status'])
        exit(3)
    else:
        return result["result"]

#parse arguments
parser = argparse.ArgumentParser(usage='%(prog)s pdf_file [options]', description='download all submissions of a gym contest')
parser.add_argument('--credential', type=str, default='./credential.json', help='credential json file location')
parser.add_argument('--output',  type=str, default='./output/', help='output directory, default is ./output/')
parser.add_argument('--submissions', type=str, help='submissions json file location')
parser.add_argument('gym_id', type = int, help='the gym to download, e.g. 482680')
args = parser.parse_args()

if args.submissions is not None and os.path.exists(args.submissions):
    info('Using submissions json file: ' + os.path.abspath(args.submissions))
    with open(args.submissions, 'r') as f:
        submissions = json.load(f)
    info('Loaded %d Submissions'%(len(submissions)))
else:
    if os.path.exists(args.credential) == False:
        error("credential file doesn't exist: " + os.path.abspath(args.credential))
        exit(1)
    cred = load_credential_json(args.credential)
    info("credential found.")

    info('Requesting full STATUS')
    submissions = get_submissions(args.gym_id, cred)
    info('Got %d Submissions'%(len(submissions)))

output_root = args.output
if output_root[-1] != '/':
    output_root = output_root + '/'

if os.path.exists(args.output) == False:
    info('Output Home not exsited, create it: ' + os.path.abspath(args.output))
    os.mkdir(args.output)

with open(args.output + 'submissions.json', 'w') as f:
    json.dump(submissions, f)

def get_input(message):
    inp = ''
    while inp not in ('y', 'n'):
        inp = input(message).lower()
    return inp == 'y'
cf_handle = None
cf_password = None
def login(session):
    global cf_handle, cf_password
    if cf_handle is None:
        cf_handle = input('Enter your codeforces handle: ')
        cf_password = getpass.getpass('Enter your codeforces password: ')
    page = session.get('https://codeforces.com/enter')
    if '403 Forbidden' in page.text:
        error('IP Blocked')
        raise IPBlockedException()
    soup = bs(page.text, 'html.parser')
    time.sleep(2)
    data = {}
    token = soup.find('input', {"name":"csrf_token"})["value"]
    data['handleOrEmail'] = cf_handle
    data['password'] = cf_password
    data['csrf_token'] = token
    data['action'] = 'enter'
    result = session.post('https://codeforces.com/enter', data=data)
    soup = bs(result.text, 'html.parser')
    if 'Invalid handle/email or password' in result.text:
        error('Invalid handle/email or password')
        return False
    if soup.find('input', {'name': 'handleOrEmail'}) is not None:
        error('Unknown error')
        return False
    return True

class IPBlockedException(Exception):
    pass

def get_source_code(session, sub):
    url = 'https://codeforces.com/gym/%s/submission/%s'%(sub['contestId'], sub['id'])
    page = session.get(url)
    if '403 Forbidden' in page.text:
        error('IP Blocked')
        raise IPBlockedException()
    soup = bs(page.text, 'html.parser')
    code_area = soup.find(id = 'program-source-text')
    if code_area is None:
        with open(output_root + 'error.html', 'w') as f:
            f.write(page.text)
        error("Failed to get source code for %s's submission %d for problem %s"%(sub['author']['members'][0]['handle'], sub['id'], sub['problem']['index']))
        return None
    return code_area.text

def get_extension(sub):
    for key, value in extensions:
        if key in sub['programmingLanguage']:
            return value
    warn("Unknown language" + sub['programmingLanguage'] + "of %s's submission %d for problem %s. Saving it as txt"%(sub['author']['members'][0]['handle'], sub['id'], sub['problem']['index']))
    return 'txt'

def download_submission(session, sub):
    problem = sub['problem']["index"]
    problem_root = output_root + problem + '/'
    if os.path.exists(problem_root) == False:
        info('Problem %s Home not exsited, create it: '%(problem) + os.path.abspath(problem_root))
        os.mkdir(problem_root)
    ext = get_extension(sub)
    author = sub['author']['teamName'] if 'teamName' in sub['author'] else sub['author']['members'][0]['handle']
    sub_path = problem_root + sub['verdict'] + '_' + author + '_' + str(sub['id']) + '.' + ext
    if os.path.exists(sub_path):
        info('Skipped ' + sub_path)
        return False
    source_code = get_source_code(session, sub)
    if source_code is None:
        raise Exception('Failed to get source code')
    with open(sub_path, 'w') as f:
        f.write(source_code)
    info('Downloaded ' + sub_path)
    return True

def main():
    global cf_handle, cf_password
    succeed = 0
    count = 0
    time_start = time.time()
    with requests.Session() as session:
        while not login(session):
            if not get_input('Try again? (y/n)'):
                exit(4)
            else:
                cf_handle = input('Enter your codeforces handle: ')
                cf_password = getpass.getpass('Enter your codeforces password: ')
        for sub in submissions:
            chk_before = time.time()
            for retry in range(3):
                try:
                    downloaded = download_submission(session, sub)
                    succeed = succeed + 1
                except IPBlockedException:
                    change_account = None
                    try:
                        change_account=inputimeout(prompt='IP Being Blocked, Input ANY KEY to change account. Will use the same account after 10s if no action:', timeout=10)
                    except TimeoutOccurred:
                        pass
                    finally:
                        if change_account is not None:
                            cf_handle = input('Enter your new codeforces handle: ')
                            cf_password = getpass.getpass('Enter your new codeforces password: ')
                        else:
                            warn('IP Blocked. Retry after 60s with the same account.')
                            time.sleep(60)
                    return False
                except Exception as e:
                    warn('Download failed: ' + str(e))
                    time.sleep(2)
                    continue
                break
            count = count + 1
            if downloaded:
                time.sleep(2 + random.random() * 3)
            chk_after = time.time()
            duration = int(chk_after - chk_before)
            passed = int(chk_after - time_start)
            et = int(1.0 * passed / count * (len(submissions) - count))
            info('[%d/%d] Processed. %d Succeeded.'%(count, len(submissions), succeed))
            if count % 10 == 0:
                info('Time Escaped %ds. ET: %ds.'%(passed, et))
    
    print('Done. Succeed: %d, Total: %d'%(succeed, len(submissions)))

while not main():
    pass

