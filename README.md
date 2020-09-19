# python-bdr-tse

python-bdr-tse is a Python package implementing the [Bundesdruckerei TSE](https://www.bundesdruckerei.de/de/loesungen/Fiskalisierung) transport
layer protocol. This device is designed as an add-on to electronic
cashier systems to make them conforming the the German [KassenSichV](https://de.wikipedia.org/wiki/Kassensicherungsverordnung)
regulation, which requires transactions to be consecutively numbered and
cryptographically signed.

Good documentation on KassenSichV, GoBD requirements for electronic cashier systems
and  how these various requirements interact is provided in a document by Deutscher
Fachverband für Kassen- und Abrechnungssystemtechnik e.V.: [Zusammenstellung der
Beschlüsse und Bundeskonventionen zu den Standardtabellen im Bereich der
 Kassenbuchhaltung - Digitale Schnittstelle der Finanzverwaltung für Kassensysteme
  (DSFinV-K)](https://dfka.net/wp-content/uploads/2019/08/20190802_DSFinV_K_V_2_0.pdf)

## General usage

Communication with the TSE happens by means of a special file in the user-accessible
partition of the TSE. In production, you will probably want to mount the TSE at a
stable path.

```python
import bdr_tse

tse = bdr_tse.TseConnector(tse_path="/media/tse")
```

Documentation (scarce, but hopefully growing) is available at https://python-bdr-tse.readthedocs.io/

## Command Line Interface

python-bdr-tse ships with a simple CLI that more or less directly exposes the TSE
commands. When installed with pip, just run `bdr-tse`.

## Contributing

### Reporting issues

Please use the Github Issue Tracker to report issues.

### Code Style

python-bdr-tse uses the [Black](https://github.com/psf/black) code formatter. Use
 `pre-commit install` to install it as a git pre-commit hook.

### Vendor Documentation

Documentation about the protocol can be downloaded from [cryptovision's website
](https://tse-support.cryptovision.com). Engineering samples can be obtained from
[Jarletch](https://www.jarltech.com). These samples differ from production device in
that they can be factory reset.
