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