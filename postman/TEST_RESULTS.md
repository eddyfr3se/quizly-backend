# Authentication test results

Date: 25 November 2026. Scope: Day 3, registration and cookie login.

| Check | Result |
| --- | --- |
| Django test suite | 23 tests passed |
| Postman CLI 1.73.0 | 33 requests, 99 assertions passed; zero failures |
| Django migration check | No model changes detected |
| PEP 8 check | New authentication API and test files passed pycodestyle |
| Function length check | All authentication functions and methods at most 14 lines, including docstrings |
| Browser check | Frontend registration, login, redirects and HttpOnly cookie storage passed |

## Django coverage

- Registration success and exact response fields; hashed password storage.
- Required, blank and null fields; invalid email/username; duplicate username
  and case-insensitive duplicate email; password confirmation; malformed JSON.
- Preservation of password whitespace and rejection of privilege escalation.
- Login success and exact response fields, with no password or token in JSON.
- JWT signatures, account identifiers, token types, unique token identifiers
  and access/refresh lifetimes.
- HttpOnly, SameSite, Path, Max-Age and Secure cookie settings.
- Wrong password, unknown user and inactive account use the same HTTP 401 error.
- Repeated login, stale cookies/headers and unsupported HTTP methods.
- Origin restrictions and credentialed frontend CORS preflights.

## Postman run

Executed the saved collection using the local Postman CLI with
`--no-report-events`, against `http://127.0.0.1:8001/api/`.
The temporary server used a fresh disposable SQLite database, separate from
the existing development server on port 8000. No Postman account was used.

The collection checks registration, duplicate and malformed input, required
fields, credential failures, rejected origins/methods and successful login.
It inspects both Set-Cookie headers and decoded JWT claims. Signature
verification and inactive-user behavior are covered by Django tests.
Runtime credentials and cookie values are not stored in the collection.

Registration and login were checked off in the official endpoint documentation
in Safari after the successful runs. The other seven operations remain open.

## Remaining scope

The browser check used a temporary copy of the supplied frontend on port 5500,
with only its API address changed to the disposable backend on port 8001.
Registration returned 201 and redirected to login; login returned 200 and
redirected to the library. Browser inspection confirmed both cookies have
HttpOnly=true, SameSite=Lax, Path=/ and Secure=false for local HTTP.
`document.cookie` was empty. No token values were included in the report.

The library's quiz-list request returned 404 because quiz endpoints are not
implemented yet. Protected cookie authentication, refresh and logout follow
on Day 4; the complete quiz workflow follows later. No official Academy test
collection or project-wide acceptance result is claimed.
