import csv
import pygit2
import time


def parse_shas(bug_inducing_shas):
    formatted = bug_inducing_shas

    if bug_inducing_shas[0] == '\"':
        formatted = formatted.strip('\"')
    elif bug_inducing_shas[0] == '[':
        formatted = formatted[1:-1]

    return formatted.split(",")


def is_java(fpath):
    return fpath[-4:] == "java"


def want_to_skip(line):
    test = line.lstrip()

    return not test or test[:2] == "/*" or test[0] == '*' or test[:7] == "package" or test[:6] == "import" or test[0] == "@" or test[:2] == "//"


def prem_task(project, repo, commit, sha, csv_writer):
    date = time.strftime("%Y-%m-%d", time.gmtime(commit.commit_time))

    try:
        diff = repo.diff(commit.parents[0], commit, context_lines=0)
    except IndexError:
        # This occurs when the blamed commit is the initial commit
        # We'll have enough data so we'll just skip it
        return

    for patch in diff:
        old_file = patch.delta.old_file.path

        if not is_java(old_file):
            continue

        for hunk in patch.hunks:
            for line in hunk.lines:
                if line.origin == '+':
                    line_no = line.new_lineno

                    # skip comments, import statements, package statements, whitespace only lines, annotations
                    if want_to_skip(line.content):
                        continue

                    csv_writer.writerow([project, date, sha, old_file, line_no])


# This function iterates over the commits in a csv file and does some task on it which can be written to an
# output csv file
def scrape(project, pos_of_sha, inputf, outputf, task):
    repo_path = project
    repo = pygit2.Repository(repo_path)

    with open(inputf) as icsvfile:
        with open(outputf, "a+") as ocsvfile:
            readCSV = csv.reader(icsvfile, delimiter='\t')
            writeCSV = csv.writer(ocsvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            for row in readCSV:
                bug_inducing_shas = row[pos_of_sha]

                # ignore header in csv file
                if bug_inducing_shas == 'BugInducingCommit':
                    continue

                for sha in parse_shas(bug_inducing_shas):
                    sha = sha.lstrip()

                    try:
                        commit = repo.revparse_single(sha)
                    except Exception:
                        print("Skipping commit", sha, "in project", project)
                        continue

                    task(project, repo, commit, sha, writeCSV)


def scrape_szz_labelled(project):
    input_csv_path = project + "/AG_SZZ.txt"
    output_csv_path = "_nonbugs.csv"

    scrape(project, 1, input_csv_path, output_csv_path, prem_task)


def scrape_dev_labelled(project):
    input_csv_path = project.upper() + ".csv"
    output_csv_path = "_bugs.csv"

    scrape(project, 2, input_csv_path, output_csv_path, prem_task)


for project in ["accumulo", "ambari", "hadoop", "lucene", "oozie"]:
    scrape_dev_labelled(project)
    scrape_szz_labelled(project)
