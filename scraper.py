import csv
import pygit2

def parse_shas(bug_inducing_shas):
    return bug_inducing_shas.strip('\"').split(",")

def scrape(repo_path, input_csv_path, output_csv_path):

    repo = pygit2.Repository(repo_path)

    with open(input_csv_path) as icsvfile:
        readCSV = csv.reader(icsvfile, delimiter='\t')

        for row in readCSV:
            bug_inducing_shas = row[2]

            #ignore first row
            if bug_inducing_shas == 'BugInducingCommit':
                continue

            for sha in parse_shas(bug_inducing_shas):
                commit = repo.revparse_single(sha)
                time = commit.commit_time

                diff = commit.getDiff(repo)





scrape("./accumulo", "ACCUMULO.csv", "")
