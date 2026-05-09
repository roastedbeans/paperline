# Draw.io Figure Design Guidelines

## Canvas Setup

Set these on every new diagram via the page properties.

| Property | Value |
| --- | --- |
| `background` | `#ffffff` |
| `pageWidth` | `1100` |
| `pageHeight` | `1400` |
| `grid` | `1` |
| `gridSize` | `10` |
| `math` | `0` |
| `shadow` | `0` |

---

## Grid and Spacing

All coordinates and dimensions must be multiples of the grid size so every element snaps cleanly to the grid.

| Rule | Value |
| --- | --- |
| Grid size | `10px` |
| All `x`, `y`, `width`, `height` | multiples of `10` |
| Gap between adjacent section containers | `10px` (1 grid space) |
| Internal section padding | `10px` top and `10px` bottom |

### Message Slot Anatomy (sequence diagrams)

Each message in a sequence diagram has up to three layers stacked vertically: a **label** above the arrow (the main message name), the **arrow** itself, and an optional **subtitle** below the arrow (parenthesized supplementary detail such as IEs or identifiers).

To keep label and subtitle text snug against the arrow, both text cells share an edge with the arrow line, and `verticalAlign` pulls the text toward that shared edge.

| Element | `y` | `h` | `verticalAlign` | Text renders at |
| --- | --- | --- | --- | --- |
| Label (above arrow) | `slot_y` | `20` | `bottom` | bottom of cell = arrow `y` |
| Arrow | `slot_y + 20` | — | — | the arrow line itself |
| Subtitle (below arrow) | `slot_y + 20` (= arrow `y`) | `20` | `top` | top of cell = arrow `y` |

The subtitle cell starts at the **same** `y` as the arrow (not `arrow_y + 10`). With `verticalAlign=top` and the cell top sharing the arrow's `y`, the subtitle text sits flush against the arrow with only the renderer's small internal padding between them. A 10px gap between arrow and subtitle cell is too loose and breaks the message-as-unit reading.

Label text styling:

| Layer | `fontSize` | `fontStyle` | `fontColor` |
| --- | --- | --- | --- |
| Label | `12` | normal (`0`) | `#212121` |
| Subtitle | `11` | italic (`2`) | `#7a378b` |

### Inter-Slot Spacing (post-content gap)

The space between two consecutive messages depends only on whether the **upper** message has a subtitle. The lower message contributes nothing — it always starts with a label.

| Upper message ends with | Post-content gap | Reasoning |
| --- | --- | --- |
| Subtitle (with-sub) | `10px` (1 grid space) | subtitle text already visually separates the messages |
| Arrow (no-sub) | `30px` (3 grid spaces) | extra room reserves the absent subtitle's visual slot |

Slot pitch (consecutive label `y` distance) is **always `50px`** as a result:

- with-sub case: `20` label + `20` subtitle + `10` gap = `50`
- no-sub case: `20` label + `30` gap = `50` (the arrow itself has zero height; it sits on the label's bottom edge)

Same-pitch is what makes columns of mixed message types still align in a clean rhythm.

### Section Height Calculation

Section height accounts for top padding, slot pitches, the last slot's content, and bottom padding. Top padding is always `10px`. Bottom padding follows the same rule as the inter-slot gap, applied to the **last** message:

| Last message ends with | Bottom padding |
| --- | --- |
| Subtitle (with-sub) | `10px` |
| Arrow (no-sub) | `30px` |

```text
section_h = 10                                  # top padding
          + (N - 1) × 50                        # all but last slot at 50px pitch
          + last_slot_content_h                 # 40 if subtitle, 20 if not
          + bottom_padding                      # 10 if last has subtitle, 30 if not
```

The asymmetric bottom padding reserves the absent subtitle's slot so consecutive sections feel evenly weighted regardless of their last message type.

Examples from `lte-signaling-sequence.drawio`:

| Section | Slots | Pattern | Computed `h` |
| --- | --- | --- | --- |
| PHY | 1 (with sub) | `10 + 40 + 10` | `60` |
| SysInfo | 1 (with sub) | `10 + 40 + 10` | `60` |
| MAC | 2 (no sub, with sub) | `10 + 50 + 40 + 10` | `110` |
| RRC | 2 (with sub, no sub) | `10 + 50 + 20 + 30` | `110` |
| NAS | 5 (all with sub) | `10 + 4×50 + 40 + 10` | `260` |
| EPS Bearer | 1 (with sub) | `10 + 40 + 10` | `60` |

### Background Containers (sequence diagrams)

Sequence diagram sections use two layers: a solid section label on the far left (`x=10 w=80`) and a dashed background container that spans the message area (`x=100`).

Section labels sit **2 grid spaces (16px) to the left** of the background container. The background container extends **3 grid spaces (30px) on both sides** of the lifeline span — 30px before the first lifeline and 30px after the last lifeline.

| Element | `x` | `width` | Right edge | Notes |
| --- | --- | --- | --- | --- |
| Section label | `70` | `80` | `150` | Right edge = container `x` − 20 |
| Narrow background (UE–E-UTRAN) | `170` | `320` | `490` | `200−30` to `460+30` |
| Wide background (UE–EPC) | `170` | `580` | `750` | `200−30` to `720+30` |

Background containers use `dashed=1; strokeWidth=1` with the section's accent color as `strokeColor`. They must be listed first in the XML so they render behind all other elements.

---

## Tree / Taxonomy Diagrams

Hierarchical figures (taxonomies, attack trees, classification trees) use a tighter grid than sequence diagrams. Every parent–child and sibling–sibling gap is exactly **3 grid spaces (`30px`)** so the tree reads as one densely packed unit rather than scattered boxes.

### Box dimensions

| Element | `width` | `height` | Notes |
| --- | --- | --- | --- |
| Root (main) | `180` | `40` | Single box at the top of the tree |
| L2 parent (e.g., Passive / Active) | `160` | `40` | Direct children of root |
| L3 sub-category | `140` | `40` | Intermediate parents inside a sub-tree |
| Leaf | `140` – `160` | `40` | Terminal nodes; choose width to match the column above it |

All taxonomy boxes use `h=40` (one grid space shorter than sequence-diagram boxes). The shorter height keeps multi-row trees compact.

### Spacing rule (3-grid uniform)

| Gap | Distance |
| --- | --- |
| Root bottom → L2 top | `30px` |
| L2 bottom → L3 top | `30px` |
| L3 bottom → first leaf top | `30px` |
| Consecutive sibling leaves (vertical) | `30px` |
| Consecutive sibling sub-categories (horizontal) | `30px` |

There is no inter-section padding inside a taxonomy — every box is exactly 30px from its neighbors. This is the single defining metric for taxonomy layouts; deviating from `30px` reads as misalignment.

### Text hierarchy

| Tier | `fontSize` | `fontStyle` | `fontColor` |
| --- | --- | --- | --- |
| Root (main) | `20` | Bold (`1`) | `#212121` |
| Parent (L2 or sub-category) | `16` | Bold (`1`) | accent color |
| Leaf (child) | `16` | Normal (`0`) | `#212121` |

Same size for parent and child (`16`) — bold is what carries the parent–child distinction. The root steps up to `20` to anchor the figure visually. This is one tier shorter than the sequence-diagram hierarchy (`20 / 16 / 14`) because taxonomies don't carry a subtitle layer.

### Connectors

Tree edges use `endArrow=none; strokeWidth=1`. Two routing patterns:

1. **Parent → multiple children:** L-shaped edges with explicit waypoints. Each edge exits the parent's bottom-center, drops to a shared trunk `y` halfway between the rows (`parent_bottom + 15`), traverses horizontally to the child's `x`, then drops to the child's top-center. Multiple edges sharing the same trunk `y` form a clean tree fork.

2. **Single parent → vertically stacked children (within one column):** A single vertical "trunk" line from `(col_x, parent_bottom)` to `(col_x, last_child_bottom)`. The line is drawn **before** the child boxes in the XML so the boxes render on top — only the inter-child gaps reveal the trunk. This avoids drawing N edges that all overlap.

Trunk `strokeColor` matches the sub-tree's accent color (gray for neutral, blue/purple/amber/red for typed sub-trees) so the eye can follow each branch even when trunks cross at the L1→L2 fan-out.

### Element ID naming for taxonomies

| Prefix | Applies to | Example |
| --- | --- | --- |
| `n_` | Root node | `n_root` |
| `c_` | L2 category | `c_passive`, `c_active` |
| `s_` | L3 sub-category | `s_mitm`, `s_dos` |
| `l_` | Leaf node | `l_passive_imsi`, `l_dos_jam` |
| `trunk_` | Vertical trunk line under a parent | `trunk_passive` |
| `e_src_tgt` | L-shaped fan-out edge | `e_root_passive`, `e_active_dos` |

---

## Signal / Timing Diagrams

Diagrams that visualize radio signals across time slots (overshadow attacks, sniffing, time-frequency interactions) follow a layered horizontal layout. Each actor (transmitter, victim, receiver) gets one row with three layers stacked vertically: an icon plus label on the left, a row of time-slot rectangles, and a waveform below the rectangles.

### Layout

| Element | Position | Notes |
| --- | --- | --- |
| Title | Top center | `20` bold |
| Time arrow | Top right of slot grid | `Time →` italic gray, `12` |
| Column headers | Above first row's slots | `SF 0`, `SF 1`, ... bold gray, `14` |
| Actor icon | Left of each row | drawio shape (`mxgraph.networks.radio_tower`, `mxgraph.networks.cell_phone_1`, etc.) |
| Actor label | Right of icon | `14` bold, two-line via HTML `<br>` |
| Time-slot box | Aligned to column | `90 × 60` rectangle, colored fill, no inner label |
| Signal wave | Below the slot row | curved edge with waypoints, `~20px` below the box |
| Vertical alignment line | Through column of interest | dashed accent color, spans header to last wave |
| Annotation | Below relevant element | `12` italic, accent color |
| Caption | Bottom of figure | `14` normal `#444444`, full width |

### Time-slot grid

| Property | Value |
| --- | --- |
| Slot box `width` | `90` |
| Slot box `height` | `60` |
| Horizontal gap between slots | `20` |
| Vertical gap between slot row and wave below it | `20` |
| Vertical gap between rows | `30` (3 grid spaces, matches taxonomy spacing) |

The slot rectangles carry the time-slot color (blue for legitimate, red for malicious, dashed gray for silent). They are intentionally label-free. Column headers above the first row identify the slot index, and color identifies the source.

### Signal waves (curved edges with waypoints)

Sine-wave shapes from external stencil libraries (`mxgraph.electrical.waveforms.*`) do not render reliably across all drawio builds. Use **curved edges with alternating waypoints** instead. They are part of drawio core and render in every version (desktop, web, VS Code extension).

Wave geometry recipe:

- Style: `endArrow=none; html=1; curved=1; strokeColor=<accent>; strokeWidth=1.5`
- Source and target points: at the wave's two endpoints, both at the row's centerline `y`
- Waypoints: alternating `(x, centerline_y - 10)` and `(x, centerline_y + 10)`, spaced `20` apart on the x-axis
- For a wave spanning `W` pixels, use roughly `W / 20` waypoints. Round to an even number so the wave ends symmetrically at the centerline

Three wave shapes by purpose:

| Wave type | `strokeColor` | `strokeWidth` | Waypoint pattern | Use for |
| --- | --- | --- | --- | --- |
| Continuous transmission | `#1f77b4` (blue) | `1.5` | dense, full row width | Legitimate cell signal across all slots |
| Padded burst | `#c0504d` (red) | `2.0` | dense, only at the active slot | Attacker injecting at one slot |
| Mixed segments | mix of `#1f77b4` and `#c0504d` | `1.5` and `2.0` | one wave per color region, joined at slot boundaries | Receiver's decoded combined signal |

### Padding (silence indicators)

When an actor stays silent at certain slots, draw a **dashed gray flat line** at the row centerline across the silent x-range. Pair the silent regions with one italic gray label such as `silence (no Tx)`.

| Element | Style |
| --- | --- |
| Padding line | `endArrow=none; strokeColor=#cccccc; dashed=1; strokeWidth=1` |
| Padding label | `text; fontSize=11; fontStyle=2; fontColor=#888888` |

The flat dashed line at the centerline keeps the eye on the same axis level as the active wave next to it. The contrast between flat silence and oscillating transmission becomes immediate.

### Vertical alignment line

When the figure highlights one column (e.g., the overshadowed subframe), draw a dashed accent-color vertical line through that column's center. The line spans from above the first row's content down to below the last row's wave. This anchors the eye to the column being discussed across all rows.

| Property | Value |
| --- | --- |
| Style | `endArrow=none; strokeColor=<accent>; dashed=1; strokeWidth=1` |
| `x` | center of the highlighted column |
| `y` range | from `header_y - 5` to `last_wave_y + 25` |

### Element ID naming for signal/timing diagrams

| Prefix | Applies to | Example |
| --- | --- | --- |
| `t_` | Title, annotation, caption text | `t_title`, `t_overshadow_label`, `t_caption` |
| `hdr_` | Column header | `hdr_sf0`, `hdr_sf2` |
| `icon_` | Actor icon shape | `icon_cell`, `icon_attacker`, `icon_ue` |
| `l_` | Actor text label | `l_cell`, `l_attacker`, `l_ue` |
| `<actor>_<slot>_box` | Time-slot rectangle | `cell_sf2_box`, `att_sf2_box` |
| `<actor>_*_wave` | Signal wave edge | `cell_long_wave`, `ue_wave_left`, `att_sf2_wave` |
| `<actor>_pad_*` | Silence padding line | `att_pad_left`, `att_pad_right` |
| `signal_` | Transmission flow arrow from icon to slots | `signal_cell`, `signal_attacker` |
| `line_align` | Vertical column-alignment line | `line_align` |

---

## Element ID Naming Convention

Use a consistent prefix so IDs are self-documenting inside the XML.

| Prefix | Applies to | Example |
| --- | --- | --- |
| `c_` | Container / group box | `c_security` |
| `s_` | Node (state, event, entity) | `s_auth_req` |
| `e_src_tgt` | Edge from source to target | `e_s5_s13` |

---

## Container / Group Boxes

Containers group related nodes into logical sections. Use a near-white tinted fill so sections are visually distinct without competing with node colors.

| Property | Value |
| --- | --- |
| `shape` | `rounded=0` |
| `whiteSpace` | `wrap` |
| `html` | `1` |
| `strokeColor` | `#888888` |
| `verticalAlign` | `top` |
| `collapsible` | `0` |
| `container` | `0` |
| `fontStyle` | `1` (bold) |
| `fontSize` | `15` |
| `fontColor` | `#212121` |
| `spacingLeft` | `12` when title is left-aligned |

### Section Fill Colors

Choose one tint per section. Tints must be **very close to white** so the section reads as a subtle wash and node fills (or message text on a sequence diagram) remain the dominant visual element. The accent comes from the section's `strokeColor`, not its fill.

| Hue | `fillColor` | `strokeColor` (accent) | Use for |
| --- | --- | --- | --- |
| Neutral gray | `#fafafa` | `#888888` | Idle, release, terminal, neutral / entry sections |
| Blue | `#fafcfe` | `#1f77b4` | Primary flow sections |
| Green | `#f8fcf8` | `#22b427` | Success, verification, security, NAS / registration |
| Amber | `#fefdfa` | `#d95f02` | Context reuse, optional paths, bearer / session |
| Purple | `#fcfafe` | `#7a378b` | Negotiation, capability, metadata |
| Red / pink | `#fefafa` | `#c0504d` | Error, recovery, failure paths |
| White | `#ffffff` | `#999999` | Legend, reference, annotation boxes |

Each fill is within ~5% of pure white. Pair the fill with the corresponding accent `strokeColor` (and matching `fontColor` on the section label) to keep the hue consistent across the section's visual elements.

### Nested Sections

When a section must live visually inside another section, wrap it in a group cell rather than nesting draw.io containers. The group cell has no fill or border of its own; only the inner container box carries the visual style.

```xml
<mxCell id="group_id" value="" style="group;" connectable="0" vertex="1" parent="1">
    <mxGeometry x="10" y="490" width="200" height="220" as="geometry"/>
</mxCell>
<mxCell id="c_inner" value="Section Title" style="rounded=0;whiteSpace=wrap;html=1;
    fillColor=#fdf5f4;strokeColor=#888888;verticalAlign=top;fontStyle=1;fontSize=15;
    container=0;collapsible=0;fontColor=#212121;" parent="group_id" vertex="1">
    <mxGeometry width="200" height="220" as="geometry"/>
</mxCell>
```

---

## Node Boxes

Nodes represent discrete states, events, or entities. Use stronger fills and matched stroke colors to stand out against container backgrounds.

| Property | Value |
| --- | --- |
| `shape` | `rounded=1` |
| `whiteSpace` | `wrap` |
| `html` | `1` |
| `fontSize` | `13` |
| `fontColor` | `#212121` |
| `height` | `40` (standard) |
| `width` | `160` – `190` |

### Node Role Colors

| Role | `fillColor` | `strokeColor` |
| --- | --- | --- |
| Primary / initiator | `#d6e9f8` | `#1f77b4` |
| Secondary / responder | `#fce4c4` | `#d95f02` |
| Compound / joint | `#ecd9f5` | `#7a378b` |

Apply roles consistently within a figure. Do not mix hues across roles.

---

## Edges / Arrows

All edges use `endArrow=classic; html=1` as the base style.

| Flow type | `strokeColor` | `strokeWidth` | `dashed` |
| --- | --- | --- | --- |
| Normal / primary flow | `#444444` | `1.5` | no |
| Alternative / optional flow | `#7a378b` | `1.2` | yes |
| Error / recovery flow | `#d95f02` | `1.2` | yes |

Edge labels use `fontSize=13; fontColor=#212121; labelBackgroundColor=none`.

Use `exitX / exitY` and `entryX / entryY` to pin connection points when the default auto-routing produces crossings or ambiguous paths.

---

## Typography

| Element | `fontSize` | `fontStyle` | `fontColor` |
| --- | --- | --- | --- |
| Lifeline label (column header `h_*`, top of canvas) | `20` | Bold (`1`) | `#212121` |
| Left-side label (section label `c_*`, left of background) | `16` | Bold (`1`) | accent color |
| Message label (above arrow) | `16` | Normal (`0`) | `#212121` |
| Subtitle (below arrow) | `14` | Italic (`2`) | `#7a378b` |
| Node label (state diagram) | `13` | Normal (`0`) | `#212121` |
| Edge label | `13` | Normal (`0`) | `#212121` |

Three-tier hierarchy:

- **Lifeline labels at `16px` bold** sit above the diagram as the top framing chrome — these are the largest text in the figure because they identify the actors (UE, NG-RAN, 5GC, etc.) that own the columns below.
- **Left-side labels and message text both at `16px`** form the body. Left-side labels are distinguished from message text by **bold + accent color** rather than by size, so they stay visually aligned with the messages they group rather than competing with the lifeline labels above.
- **Subtitles at `14px` italic** step down again as parenthetical supporting detail.

Body text uses `#212121` (near-black) for consistent contrast. Subtitles use `#7a378b` (purple) and italic to mark them as supplementary detail. Left-side labels use the section's accent color in the `fontColor` field, matching its `strokeColor`.

---

## Legend

Every figure includes a legend box positioned at the top of the canvas, above the diagram body.

| Property | Value |
| --- | --- |
| `fillColor` | `#ffffff` |
| `strokeColor` | `#999999` |
| `fontStyle` | `1` (bold) |
| `fontSize` | `15` |
| `align` | `center` |

The legend must show each node role used in the figure with the same `fillColor` and `strokeColor` as the actual nodes. Do not introduce colors in the legend that do not appear in the diagram.
