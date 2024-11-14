#!/usr/bin/env python
# Copyright (c) 2021 Waabi Innovation. All rights reserved.

import argparse
import logging
import time
import zipfile
import requests
from io import BytesIO
import os

from ghapi.all import GhApi, github_token

_logger = logging.getLogger(__name__)


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--commit-sha", required=True)
    args = parser.parse_args()
    _logger.info("collecting artifacts for %s", args)

    gh = GhApi(token=github_token())

    for _ in range(2):
        time.sleep(2)
        if _download_artifacts_for_run(gh, args):
            break
    else:
        raise RuntimeError("maximum attempts exceeded")

def _download_artifact(url, filename):
    """
    Download GitHub API artifact.

    Args:
    url (str): Artifact URL.
    token (str): GitHub personal access token.
    filename (str): Output filename.
    """
    token = os.environ["GITHUB_TOKEN"]
    headers = {
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Artifact downloaded successfully: {filename}")
    else:
        print(f"Failed to download artifact. Status code: {response.status_code}")


def _download_artifacts_for_run(gh, args):
    runs = gh.actions.list_workflow_runs(
        owner=args.owner,
        repo=args.repo,
        workflow_id=args.workflow_id,
        per_page=100
    )

    for run in runs.workflow_runs:
        if run.head_sha != args.commit_sha:
            _logger.debug("ignoring run %s for %s", run.id, run.head_sha)
            continue
        artifacts = gh.actions.list_workflow_run_artifacts(
            owner=args.owner,
            repo=args.repo,
            run_id=run.id,
        )
        if not artifacts.artifacts:
            _logger.warning("no artifacts available for run")
            return False
        for artifact in artifacts.artifacts:
            print("DBG", artifact, run.id)
            _download_artifact(artifact.archive_download_url, artifact.name + ".zip")
            data = gh.actions.download_artifact(
                owner=args.owner,
                repo=args.repo,
                artifact_id=artifact.id,
                archive_format="zip",
            )
            _logger.info("extrating artifact: %s", artifact.name)
            zipfile.ZipFile(BytesIO(data)).extractall(path=artifact.name)
        return True

    _logger.warning("run not found for %s", args.commit_sha)
    return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(filename)s:%(lineno)d] %(levelname)s: %(message)s")
    _main()
