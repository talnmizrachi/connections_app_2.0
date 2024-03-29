import datetime
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup
from flask import abort
from sqlalchemy.exc import SQLAlchemyError
from cross_functions.LoggingGenerator import Logger
from db import db
import pandas as pd
import os
from dotenv import load_dotenv
logger = Logger(os.path.basename(__file__).split('.')[0]).get_logger()

load_dotenv()

def parse_webhook(data_):
	logger.debug(f'{data_.get("id")} - parse_webhook')
	logger.debug(f"webook entering:\t {data_}")
	member = _get_member(data_)
	job = _get_job(data_)
	company = data_.get("employer", {}).get("name")
	logger.debug(f"job from data\t {job}")
	return {
		"hook_id": data_.get("id"),
		"action_type": data_.get("actionType"),
		"datetime": datetime.datetime.now(),
		"full_name": member.get("full_name"),
		"owner_cohort_value": member.get("cohort_value"),
		"email": member.get("email"),
		"job_title": job.get("title"),
		"job_url": job.get("url"),
		"job_id": job.get("id"),
		"job_description": job.get("description"),
		"company": company,
	}


# Webhooks
def _get_member(data: Dict[str, Any]) -> Dict[str, Any]:
	logger.debug(f'{data.get("id")} - get member')
	member = data.get("ownerMember", {})

	try:
		cohort_val = member.get("memberFieldValues", [{}])[0].get("value")
	except IndexError:
		logger.error(f"{data.get('id')} - Member not found: {member}")
		logger.debug(f"{data.get('id')} - data: {data}")
		cohort_val = None

	parsed = {
		"full_name": member.get("fullName", "").lower(),
		"cohort_value": cohort_val,
		"email": member.get("email", "").lower(),
	}

	return parsed


def _get_job(data: Dict[str, Any]) -> Dict[str, Any]:
	logger.debug(f'{data.get("id")} - get job info')
	job = data.get("job", {})
	description = job.get("htmlDescription", "")
	if len(description) > 0:
		soup = BeautifulSoup(description, "html.parser")
		desc = soup.get_text().strip().lower()
	else:
		desc = ""

	return {
		"title": job.get("title", "").lower(),
		"url": job.get("url"),
		'id': job.get("id"),
		"description": desc
	}


def committing_function(what_to_commit, hook_id=None):
	try:
		logger.debug(f"{hook_id} - what_to_commit:\t{what_to_commit}")
		db.session.add(what_to_commit)
		db.session.commit()
	except SQLAlchemyError as e:
		db.session.rollback()
		logger.error(f"{hook_id} - SQLAlchemyError - {e}")
		abort(500, str(e))










