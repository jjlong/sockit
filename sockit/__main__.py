import argparse
import csv
import logging
import json
import sockit
import sys

def main():

    parser = argparse.ArgumentParser(description=sockit.__doc__)

    # Basic arguments
    parser.add_argument("-v", "--version",
                        action="version",
                        version="sockit {}".format(sockit.__version__))
    parser.add_argument("-q", "--quiet",
                        action="store_true",
                        help="suppress all logging messages except for errors")
    parser.add_argument("-d", "--debug",
                        action="store_true",
                        help="show all logging messages, including debugging output")

    # Required arguments
    parser.add_argument("-i", "--input",
                        required=True,
                        help="input CSV file containing the record ID and title fields")

    # Optional arguments
    parser.add_argument("-o", "--output",
                        default="-",
                        help="output file (default: stdout) containing a JSON record per line: {'record_id': ..., 'title': ..., 'clean_title': ..., 'socs': [{'soc': ..., 'prob': ..., 'desc': ...}, ...]}")
    parser.add_argument("--record_id",
                        default=None,
                        help="field name corresponding to the record ID [default: 1-based index]")
    parser.add_argument("--title",
                        default="title",
                        help="field name corresponding to the title [default: 'title']")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)

    log = sockit.Log(__name__, "main")

    # Process the stream of input titles, and stream the output records.
    with open(args.input, "r") as fin:
        reader = csv.DictReader(fin)
        with open(args.output, "w") if args.output != "-" else sys.stdout as fout:
            for n, record in enumerate(reader, start=1):
                # Validate input record
                if args.record_id is not None:
                    if args.record_id in record:
                        record_id = record[args.record_id]
                    else:
                        log.error(f"record {n} is missing record_id field '{args.record_id}'")
                        sys.exit(-1)
                else:
                    record_id = n
                if args.title in record:
                    title = record[args.title]
                else:
                    log.error(f"record {n} is missing title field '{args.title}'")
                    sys.exit(-1)
                # Search
                clean_title = sockit.clean(title)
                socs = sockit.search(clean_title)
                norm = 1.0 / sum(socs.values())
                # Write output record
                json.dump(
                    {
                        "record_id": record_id,
                        "title": title,
                        "clean_title": clean_title,
                        "socs": [
                            {
                                "soc": soc,
                                "prob": norm*socs[soc],
                                "title": sockit.get_soc_title(soc)
                            }
                            for soc in sorted(socs, key=socs.get, reverse=True)
                        ]
                    },
                    fout
                )
                fout.write("\n")

    # Print summary stats
    log.info("processed {:d} records".format(n))

if __name__ == "__main__":
    main()
