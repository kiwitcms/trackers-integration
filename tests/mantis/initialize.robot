*** Settings ***
Library           SeleniumLibrary

*** Variables ***
${IP_ADDR}              127.0.0.1
${SERVER}               https://${IP_ADDR}:8443/mantisbt
${BROWSER}              Headless Firefox
${DELAY}                0
${LOGIN_URL}            ${SERVER}/login_page.php
${ACCOUNT_URL}          ${SERVER}/account_page.php
${INSTALL_URL}          ${SERVER}/admin/install.php
${API_TOKEN_URL}        ${SERVER}/api_tokens_page.php

*** Test Cases ***
Install Mantis BT and create API token
    Open Browser    ${INSTALL_URL}    ${BROWSER}        service_log_path=${{os.path.devnull}}
    Maximize Browser Window
    Set Selenium Speed    ${DELAY}
    Title Should Be    Administration - Installation - MantisBT

    Click Button  Install/Upgrade Database

    Location Should Be          ${INSTALL_URL}
    Wait Until Page Contains    MantisBT was installed successfully

    Go To         ${LOGIN_URL}
    Input Text    username    administrator
    Click Button  Login
    Input Text    password    root
    Click Button  Login

    Location Should Be    ${ACCOUNT_URL}
    Title Should Be       My Account - MantisBT

    Go To               ${API_TOKEN_URL}
    Title Should Be     API Tokens - MantisBT

    Input Text  token_name      Testing Kiwi TCMS integration
    Click Button        Create API Token
    Location Should Be  ${SERVER}/api_token_create.php
    Wait Until Page Contains    Token to use for accessing API

    ${token}=   Get Text        //div[@class="well"]
    Log To Console      ${token}

    [Teardown]    Close Browser
