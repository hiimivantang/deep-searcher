import argparse
import logging
from deepsearcher.configuration import Configuration, init_config
from deepsearcher.online_query import query
from deepsearcher.offline_loading import load_from_local_files, load_from_website

httpx_logger = logging.getLogger("httpx")  # disable openai's logger output
httpx_logger.setLevel(logging.WARNING)

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)  # disable warning output

def main():
    config = Configuration()  #Customize your config here
    init_config(config = config)

    parser = argparse.ArgumentParser(
        prog="deepsearcher", description="Deep Searcher."
    )
    ## Arguments of query
    parser.add_argument(
        "--query", type=str, default="", help="query question or search topic."
    )
    parser.add_argument(
        "--max_iter",
        type=int,
        default=3,
        help="Max iterations of reflection. Default is 3.",
    )

    ## Arguments of loading
    parser.add_argument(
        "--load",
        type=str,
        help="Load knowledge from a local files or from urls.",
    )
    parser.add_argument(
        "--collection_name",
        type=str,
        default=None,
        help="Destination collection name of loaded knowledge.",
    )

    parser.add_argument(
         '--output', 
         type=str, 
         default='deep-searcher-report.md',
         help='Path to the output file')
    
    args = parser.parse_args()
    if args.query:
        output_tuple = query(args.query, max_iter=args.max_iter)
        with open(args.output, 'w') as f:
            f.write(output_tuple[0])
    else:
        if args.load:
            if args.load.startswith("http"):
                load_from_website(args.load, collection_name=args.collection_name)
            else:
                load_from_local_files(args.load, collection_name=args.collection_name)
        else:
            print("Please provide a query or a load argument.")


if __name__ == "__main__":
    main()
