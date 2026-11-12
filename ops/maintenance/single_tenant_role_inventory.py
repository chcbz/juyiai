#!/usr/bin/env python3
"""Read-only evidence collection for CYF's strict single-tenant migration.

This tool intentionally has no DDL/DML mode.  It inventories every physical table
that contains ``tenant_id`` and emits only schema metadata, counts and SHA-256
fingerprints; it never writes tenant values, owners, primary keys or credentials
to stdout or to the repository.
"""
from __future__ import print_function

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import stat
import subprocess
import sys


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mysql", required=True, help="absolute mysql client path")
    parser.add_argument("--socket", required=True, help="MySQL UNIX socket")
    parser.add_argument("--schema", required=True, help="schema to inventory")
    parser.add_argument("--output-dir", required=True, help="private 0700 evidence directory")
    parser.add_argument("--defaults-file", help="optional mysql defaults file; never copied")
    return parser.parse_args()


def require_file(path, description, executable=False):
    candidate = pathlib.Path(path)
    if not candidate.exists():
        raise ValueError("{} does not exist".format(description))
    if executable and not os.access(str(candidate), os.X_OK):
        raise ValueError("{} is not executable".format(description))
    return candidate


def require_private_dir(path):
    directory = pathlib.Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(directory.stat().st_mode)
    if mode != 0o700:
        raise ValueError("output directory must be mode 0700")
    return directory


def require_private_file(path):
    candidate = require_file(path, "defaults file")
    mode = stat.S_IMODE(candidate.stat().st_mode)
    if mode & 0o077:
        raise ValueError("defaults file must not be group/world accessible")
    return candidate


def mysql_query(mysql, socket_path, schema, defaults_file, sql):
    command = [str(mysql)]
    if defaults_file:
        command.append("--defaults-extra-file={}".format(defaults_file))
    command.extend([
        "--protocol=socket", "--socket={}".format(socket_path), "-uroot",
        "--batch", "--skip-column-names", "--raw", schema, "-e", sql,
    ])
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True, check=False)
    if result.returncode != 0:
        raise RuntimeError("mysql read-only inventory query failed (exit {})".format(result.returncode))
    return [line.split("\t") for line in result.stdout.splitlines() if line]


def as_integer(value):
    return 0 if value in (None, "", "NULL") else int(value)


def quote_identifier(value):
    return "`{}`".format(value.replace("`", "``"))


def utc_plus_eight_now():
    return datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=8))).isoformat()


def main():
    args = parse_args()
    mysql = require_file(args.mysql, "mysql client", executable=True)
    socket_path = require_file(args.socket, "mysql socket")
    output_dir = require_private_dir(args.output_dir)
    defaults_file = require_private_file(args.defaults_file) if args.defaults_file else None

    tables = mysql_query(mysql, socket_path, args.schema, defaults_file, """
        SELECT c.table_name, t.table_type,
               GROUP_CONCAT(DISTINCT k.column_name ORDER BY k.ordinal_position SEPARATOR ','),
               GROUP_CONCAT(DISTINCT c.column_name ORDER BY c.ordinal_position SEPARATOR ',')
        FROM information_schema.columns c
        JOIN information_schema.tables t
          ON t.table_schema = c.table_schema AND t.table_name = c.table_name
        LEFT JOIN information_schema.key_column_usage k
          ON k.table_schema = c.table_schema AND k.table_name = c.table_name
         AND k.constraint_name = 'PRIMARY'
        WHERE c.table_schema = DATABASE() AND c.column_name = 'tenant_id'
        GROUP BY c.table_name, t.table_type
        ORDER BY c.table_name
    """)

    rows = []
    for table_name, table_type, primary_key, _tenant_columns in tables:
        item = {
            "table": table_name,
            "type": table_type,
            "primaryKey": primary_key.split(",") if primary_key else [],
            "tenantColumn": "tenant_id",
        }
        if table_type != "BASE TABLE":
            item["countStatus"] = "not-counted-view"
            rows.append(item)
            continue
        counts = mysql_query(
            mysql, socket_path, args.schema, defaults_file,
            "SELECT COUNT(*), SUM(tenant_id = '0'), SUM(tenant_id IS NULL), "
            "SUM(tenant_id <> '0' AND tenant_id IS NOT NULL), COUNT(DISTINCT tenant_id) FROM {}"
            .format(quote_identifier(table_name)))
        values = counts[0] if counts else ["0"] * 5
        item.update({
            "rowCount": as_integer(values[0]),
            "tenantZeroCount": as_integer(values[1]),
            "tenantNullCount": as_integer(values[2]),
            "tenantNonZeroCount": as_integer(values[3]),
            "distinctTenantCount": as_integer(values[4]),
        })
        rows.append(item)

    payload = {
        "schema": args.schema,
        "capturedAt": utc_plus_eight_now(),
        "mode": "read-only tenant inventory",
        "tables": rows,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
    payload["inventorySha256"] = hashlib.sha256(canonical).hexdigest()

    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    destination = output_dir / ("single-tenant-inventory-{}.json".format(stamp))
    temporary = output_dir / (".{}.tmp".format(destination.name))
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(str(temporary), 0o600)
    temporary.replace(destination)

    summary = {
        "inventory": str(destination),
        "inventorySha256": payload["inventorySha256"],
        "baseTables": sum(1 for row in rows if row["type"] == "BASE TABLE"),
        "views": sum(1 for row in rows if row["type"] != "BASE TABLE"),
        "tablesWithNonZeroTenant": sum(1 for row in rows if row.get("tenantNonZeroCount", 0) > 0),
        "rowsWithNonZeroTenant": sum(row.get("tenantNonZeroCount", 0) for row in rows),
        "rowsWithNullTenant": sum(row.get("tenantNullCount", 0) for row in rows),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("single-tenant inventory failed: {}".format(error), file=sys.stderr)
        sys.exit(2)
