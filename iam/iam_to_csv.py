# Quick script to output AWS IAM user account info to a csv file
# input: output from `aws iam get-account-authorization-details > iam.json`
from __future__ import print_function
import sys, json, pandas as pd

OUTPUT_FILE = 'iam.csv'

iam_file = sys.argv[0]
with open(iam_file, 'r') as fp:
    iam = json.load(fp)

df = pd.DataFrame.from_dict(iam['UserDetailList'])
df = df[['UserName', 'GroupList', 'CreateDate', 'UserPolicyList', 'AttachedManagedPolicies', 'Tags']]

df.to_csv(OUTPUT_FILE)

print(f"CSV outputted to {OUTPUT_FILE}")