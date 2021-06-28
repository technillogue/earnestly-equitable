#!/usr/bin/env python
# coding: utf-8
import json
from typing import Union
import maya
from splitwise import (
    Splitwise,
)  # we're using a forked version of splitwise modified to support api_key and debugging
from splitwise.expense import Expense, ExpenseUser
from splitwise.error import SplitwiseError


def parse_spreadsheet(text: str) -> dict[str, int]:
    raw_shares = [name.split(": ") for name in spreadsheet_text.split("\n")]
    shares = {
        spreadsheet_name.strip().lower(): int(share.strip())
        for spreadsheet_name, share in raw_shares
    }
    return shares


def make_expense_user_object(
    name: str, user_id: int, owed: float, paid: float = 0.0
):
    user = ExpenseUser()
    user.setFirstName(name)
    user.setId(user_id)
    user.setOwedShare(owed)
    user.setPaidShare(paid)
    return user


secrets = json.load(open("secrets.json"))
# splitwise dev provides an api key for fucking around, you're supposed to use the "sign in using..." dialog
api_key = secrets.get("api_key")
splitwise = Splitwise(
    secrets["consumer_key"], secrets["consumer_secret"], api_key=api_key
)
# logged in as sylvie, since i got the api key


groups = {group.getName(): group for group in splitwise.getGroups()}
earnest = groups["Earnest: the Jort Fort"]
name_to_splitwise_id = {
    member.first_name.lower(): member.id for member in earnest.members
}


categories = {
    category.name: category.id for category in splitwise.getCategories()
}
subcategories = {
    subcategory.name: subcategory.id
    for category in splitwise.getCategories()
    for subcategory in category.subcategories
}


may_spreadsheet_text = ...
may_shares = parse_spreadsheet(may_spreadsheet_text)
people_eating_food_in_may = ...


def create_expense(
    cost: float,
    description: str,
    human_date: str = "now",
    payer: str = "Sylvie",
    category_name: str = "Groceries",
    split_with: list[str] = people_eating_food_in_may,
    shares: dict[str, int] = may_shares,
    group_id=earnest.id,
) -> Union[Expense, SplitwiseError]:
    expense = Expense()
    expense.setCost(cost)
    expense.setDescription(description)
    robot_date = maya.when(human_date).iso8601()
    expense.setDate(robot_date)
    expense.setCategory(categories[category_name])
    effective_shares = {
        name: share
        for name, share in shares.items()
        if name in split_with or name == payer
    }
    total_shares = sum(effective_shares.values())
    owed = {
        name: round(cost * share / total_shares, 2)
        for name, share in effective_shares.items()
    }
    owed[payer] += cost - sum(owed.values())  # if payer covers the change
    users = [
        make_expense_user_object(
            name, name_to_splitwise_id[name], owes, cost if name == payer else 0
        )
        for name, owes in owed.items()
    ]
    expense.setUsers(users)
    expense.setGroupId(group_id)
    returned_expense, error = splitwise.createExpense(expense)
    if error:
        print(f"errors: {error.errors}")
        return error
    print(
        returned_expense.date.split("T")[0],
        returned_expense.cost,
        returned_expense.description,
    )
    return returned_expense


# for parsing completely unstructured text you could just search for a number, description, [payer_name_pattern, time_like, except/include_pattern]+
def parse(
    slack_msg: str, shares: Optinal[dict[str, int]]
) -> Union[Expense, SplitwiseError]:
    cost, description, date = slack_msg.split(",")
    return create_expense(float(cost), description, date, shares=shares)


# you want a convenient way of setting and useing a default for a month, but not hardcoded...
