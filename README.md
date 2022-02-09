database-reports
================

MediaWiki database reports, primarily written for the English Wikipedia:
<https://en.wikipedia.org/wiki/Wikipedia:Database_reports>.

## Dependencies
* Rust 1.56+, usually installed with [rustup](https://rustup.rs/)
* Access to WikiReplicas (see [instructions](https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database))

If you want to run these reports locally, create or copy a `~/replica.my.cnf`
file that looks roughly like this:

```
[client]
user='databaseusernamehere'
password='databasepasswordhere'
local='true'
```

Create a `~/.dbreps.toml` file that looks roughly like this:

```
[auth]
username = "wikiusernamehere"
password = "wikipasswordhere"
```

Then in a shell you can create an SSH tunnel using a command such as this:

```
ssh -N shellusernamehere@tools-login.wmflabs.org -L 3306:enwiki.analytics.db.svc.wikimedia.cloud:3306
```

## Useful commands
```
# Format your code automatically
$ cargo fmt
# Run the database reports (in debug mode)
$ cargo run
# Run a single report
$ cargo run -- --report="User categories"
# Run the clippy linter
$ cargo clippy -- -D warnings
```

## Deploying changes
```
$ become dbreps
dbreps$ cd ~/src/database-reports
dbreps$ git pull
dbreps$ ./build-rust.sh
```

## Old Python reports
These old reports need to be ported to Rust. Patches welcome!

## Licensing
License information is available in the LICENSE file.
