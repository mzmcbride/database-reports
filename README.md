database-reports
================

MediaWiki database reports, primarily written for the English Wikipedia:
<https://en.wikipedia.org/wiki/Wikipedia:Database_reports>.

## Dependencies
* Rust 1.56+, usually installed with [rustup](https://rustup.rs/)
* Access to WikiReplicas (see [instructions](https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database))

## Useful commands
```
# Format your code automatically
$ cargo fmt
# Run the database reports (in debug mode)
$ cargo run
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
