# ambient-listener
 A lifestyle app to assist in keeping an awareness of your environment.


# ambient-listener

A lifestyle app to assist in keeping an awareness of your environment.

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Introduction

Welcome to ambient-listener! This app is designed to help you stay aware of your environment and make informed decisions. It listens to your environment and provides AI powered notifications and suggestions of actions to take.

## Prerequisites

- `python 3.10` - autogen rag functionality requires some dependencies specific to py3.10



## Installation

To use ambient-listener, follow these steps:

1. Clone the repository: `git clone https://github.com/your-username/ambient-listener.git`
2. Install the dependencies: `pip install -r requirements.txt`
3. Create a file called `OAI_CONFIG_LIST` in the root directory with the following format:
```
[
    {
        "model": "choose-a-model",
        "api_key": "your-api-key-here"
    }
]
```


## Usage

To get started with ambient-listener, run the following command:

`python ambient_listener_chat.py`

## Todo
- conversation termination is a little awkward
- get actual calendar data format. come up with strategy for fetching calendar data.
  - maybe only get 1 month(+/- 2 weeks from current date)
- speech to text
- actually send notifications somewhere