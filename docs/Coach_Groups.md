Coach_Groups sheet specification
================================

Purpose
-------
This sheet describes all teams (or team sets) that share a coach. The solver uses these groups to avoid simultaneous matches for the same coach and to reward convenient consecutive matches when possible.

Sheet name (Excel): `Coach_Groups`

Column layout
-------------

- `group_id` (optional): short identifier for the group (e.g., `PARIS`). All rows must be unique; missing IDs fall back to the coach name.
- `coach_name` (required): full name or unique identifier of the coach.
- `slot_01` … `slot_20` (required, 20 columns): each slot describes one inclusion rule. In Excel you now pick friendly labels such as `Université de Paris [F]` (italicized to signal an institution) or `Lyon 1 (1) [M]`. The updater keeps supporting the legacy `team=…` / `institution=…` syntax and automatically reformats it into the friendly display on the next run. Every slot can be left blank when unused; fill as many slots as needed to cover all teams for the coach.
- `notes` (optional): free text for human readers (club information, exceptions, etc.).

Excel assistance
----------------

- Running `python scripts/update_config_excel.py --fichier <config.xlsx>` regenerates the sheet headers, applies alternating fills for quicker scanning, and injects drop-down lists in every slot column.
- Each slot now proposes readable labels (e.g., `Université de Paris [F]`, `Lyon 1 (1) [M]`) instead of the raw `team=` / `institution=` tokens. Institutions are rendered in italic with the `[F]` / `[M]` suffix so they stand out from single-team selections. If you still type the legacy syntax, the updater normalizes it into the friendly format on the next run.
- Legacy `teams` columns are automatically renamed to `EXTRA_teams` so you can copy/paste old data before deleting the column.

Validation and data hygiene
---------------------------

- Normalization: values are trimmed; `institution` comparisons are case-insensitive; `gender` accepts the same tokens as the Teams sheet.
- Duplication control: the loader expands each slot into concrete team IDs and will raise an error if the same team resolves twice inside a group or appears in multiple groups for the same coach.
- Unknown references: `team=<TEAM_ID>` must exist in the Teams sheet; missing IDs trigger errors. `institution` references must match institutions known to the data loader; otherwise a warning is emitted.
- Mixed granularity: slot rules can co-exist (e.g., institution-wide rule plus a single team override). The loader removes duplicates before solving.
- Empty rows: rows with no slots populated are ignored.

Rules and behaviour in the solver
---------------------------------

- Groups with the same `coach_name` are merged; penalties/bonuses apply exactly once per merged coach.
- Simultaneous matches inside a group trigger penalties defined by `coach_overlap_simultane_minutes`, with different coefficients for same vs different gym.
- Consecutive matches separated by [`coach_overlap_consecutif_min_minutes`, `coach_overlap_consecutif_max_minutes`] accrue bonuses to encourage clustering.
- Travel penalties (`coach_overlap_penalite_deplacement`) apply when consecutive assignments are in different gyms.
- Locked matches participate in overlap checks starting at `coach_overlap_semaine_min`.

Example CSV (excerpt)
---------------------

```csv
group_id,coach_name,slot_01,slot_02,slot_03,slot_04,slot_05,slot_06,slot_07,slot_08,slot_09,slot_10,slot_11,slot_12,slot_13,slot_14,slot_15,slot_16,slot_17,slot_18,slot_19,slot_20,notes
PARIS,Jean Dupont,Université de Paris [F],Université de Paris [M],,,,,,,,,,,,,,,,,,,All Paris squads (two genders)
LYON_F,Chloé Martin,Club Lyonnais [F],Lyon 2 (1) [F],,,,,,,,,,,,,,,,,Specific U18 added manually
UNI_COACH,Alex Lee,team=UNI-A1,team=UNI-B1,team=UNI-C2,,,,,,,,,,,,,,,,,Private university (legacy syntax kept to show compatibility)
```

Implementation notes
--------------------

- Loader expands slots left-to-right until no more data is provided; leaving blanks between filled slots is acceptable.
- Prefer warnings over hard errors for institution mismatches so the user can fix typos without breaking the pipeline, but duplicated teams remain blocking errors.
- Update `configs/coach_groups_example.csv` whenever the format evolves to keep templates aligned with this specification.
- Use the drop-down lists after each `update_config_excel` run to avoid typos; they reflect the latest institutions/teams found in `Equipes`.
