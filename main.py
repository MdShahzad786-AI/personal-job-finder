import argparse, logging
from jobhunter.pipeline import run_pipeline
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s - %(message)s')
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--send-email',action='store_true'); a=p.parse_args()
    stats,rows=run_pipeline(a.send_email)
    print('\nRUN SUMMARY')
    for k,v in stats.items():
        if k!='source_counts': print(f'{k}: {v}')
    print('\nSOURCE COUNTS')
    for k,v in stats.get('source_counts',{}).items(): print(f'{k}: {v}')
    print(f'\nunemailed_matching_jobs: {len(rows)}')
