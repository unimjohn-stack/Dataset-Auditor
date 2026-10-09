Stage ONe: Fingerprint Records
    Given a dataset records, produce a deterministic fingerprint so that the equivalent text produces the same identifier

    basic create a code unique to the text and when a similar text is entered. it matches the previous code created

    tools used: unicode, haslid, re, SHA256, NKFC, hexdigest, casefold

Stage Two: Auditing:
    This stage is going to handle/ audit answering questions against leakages; content leakages and group leakages. Leakages are basically duplications between contents or groups, 
    Duplicate records have to be rejected.
    Structure of a record:
        {
            "id": "r1",
            "group": "customer_001",
            "text": "Hello World"
        }

Stage Three:
    This stage is going to handle the splitting between data sets and each splits must be aware of the groups they are in.
    This spliting would be done using the random import
    Stable hasing is also going to be included to splitter so that on addition of new information, consistency would me maintained as splitting occurs