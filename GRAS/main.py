from github import Github
from dotenv import load_dotenv
from datetime import datetime
import csv
from os import getenv
from rich.console import Console
from rich.prompt import Prompt, Confirm

load_dotenv()

g = Github(getenv("GITHUB_SECRET"))


class GRAS:
    def __init__(self):
        self.mode = "org"
        self.age = 60

        self.console = Console()
        self.mode = Prompt.ask("mode", choices=["org", "org-team", "user"])
        self.debug = Confirm.ask("Enable debug")

        self.config = {}
        if self.mode == "org" or self.mode == "org-team":
            self.config["org"] = Prompt.ask("Please input organization name")
            if self.mode == "org-team":
                self.config["team"] = Prompt.ask("Please input team name")
        elif self.mode == "user":
            self.config["user"] = Prompt.ask("Please input username")

    def check(self):
        repo_list_with_status = []

        repos = None
        if self.mode == "team":
            repos = g.get_organization(self.config["org"]).get_team_by_slug(self.config["team"]).get_repos()
        elif self.mode == "org":
            repos = g.get_organization(self.config["org"]).get_repos()
        elif self.mode == "user":
            repos = g.get_user(self.config.get("user")).get_repos()

        self.console.print("[blue]Starting work...[/blue]")
        for repo in repos:
            repo_list_with_status.append(self.get_repo_status(repo))

        return repo_list_with_status

    def get_repo_status(self, repo):
        self.console.print(f"\nStaring work on [orange1]{repo.name}[/orange1]:")

        commits = repo.get_commits()
        try:
            for commit in commits:
                time_between_insertion = datetime.now() - commit.commit.committer.date

                if time_between_insertion.days < self.age:
                    if self.debug:
                        self.console.print("[blue] Found commit that is not"
                                           f" older than[/blue] [cyan]{self.age}[/cyan] [blue]days[/blue]"
                                           f" ( Age: [green]{time_between_insertion.days}[/green])")
                    return {'name': repo.name, 'link': repo.html_url, 'last_commit': commit.commit.committer.date}
                else:
                    if self.debug:
                        self.console.print(f"[blue] Last commit is older than[/blue] [cyan]{self.age}[/cyan] [blue]days[/blue]"
                                           f" ( Age: [red]{time_between_insertion.days}[/red])")
                    return {'name': repo.name, 'link': repo.html_url, 'last_commit': commit.commit.committer.date}
        except Exception as e:
            if self.debug:
                self.console.print(f"[red] No commits found[/red]")
            return {'name': repo.name, 'link': repo.html_url, 'last_commit': 'never'}

    @staticmethod
    def save(repos):
        with open('repositories.csv', 'w', newline='') as csvfile:
            fieldnames = ['name', 'link', 'last_commit']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            writer.writerows(repos)

    def run(self):
        # TODO: This should be changed to allow more than just list_by_team
        repositories = self.check()

        # TODO: This should be changed to allow other save methods
        self.save(repositories)


def run():
    scanner = GRAS()
    scanner.run()


if __name__ == '__main__':
    run()
