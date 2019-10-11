import csv
import pygit2
import time

def parse_shas(bug_inducing_shas):
    return bug_inducing_shas.strip('\"').split(",")

def is_java(fpath):
    return fpath[-4:] == "java"

def want_to_skip(line):
    test = line.lstrip()

    return not test or test[:2] == "/*" or test[0] == '*' or test[:7] == "package" or test[:6] == "import" or test[0] == "@" or test[:2] == "//"

#repo path is the same as the name of the project
def scrape_buggy(project):
    repo_path = project
    input_csv_path = project.upper() + ".csv"
    output_csv_path = "bugs.csv"

    repo = pygit2.Repository(repo_path)

    with open(input_csv_path) as icsvfile:
        with open(output_csv_path, "a+") as ocsvfile:
            readCSV = csv.reader(icsvfile, delimiter='\t')
            writeCSV = csv.writer(ocsvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            for row in readCSV:
                bug_inducing_shas = row[2]

                #ignore header in csv file
                if bug_inducing_shas == 'BugInducingCommit':
                    continue

                for sha in parse_shas(bug_inducing_shas):

                    try:
                        commit = repo.revparse_single(sha)
                    except KeyError:
                        print("Skipping commit", sha, "in project", project)
                        continue

                    date = time.strftime("%Y-%m-%d", time.gmtime(commit.commit_time))

                    diff = repo.diff(commit.parents[0], commit, context_lines=0)

                    for patch in diff:
                        old_file = patch.delta.old_file.path

                        if not is_java(old_file):
                            continue

                        for hunk in patch.hunks:
                            for line in hunk.lines:
                                if line.origin == '+':
                                    line_no = line.new_lineno

                                    #skip comments, import statements, package statements, whitespace only lines, annotations
                                    if want_to_skip(line.content):
                                        continue

                                    writeCSV.writerow([repo_path, date, sha, old_file, line_no, "1"])


for project in ["accumulo", "ambari", "hadoop", "jcr", "lucene", "oozie"]:
    scrape_buggy(project)
