Convert Deutsche Bahn PDF tickets to PKPass

# Usage

```sh
$ python3 -m venv .venv
$ . .venv/bin/activate
$ python3 -m pip install -r requirements.txt
$ python3 db_pkpass.py /path/to/my/ticket.pdf
```

You can also make manual adjustments before packing the pkpass file:

```sh
$ python3 db_pkpass.py /path/to/my/ticket.pdf --debug > ticket.json
$ $EDITOR ticket.json
$ python3 db_pkpass.py ticket.json
```

# Limitations

-   The PKPass file does not contain a signature, so it will not work with
    Apple Wallet
-   The code has not been extensively tested yet. There will still be many
    issues with different tickets or wallets.

# Prior Art

For a much more comprehensive solution, see https://github.com/TheEnbyperor/zuegli
