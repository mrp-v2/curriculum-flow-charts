# Curriculum Flow Charts

Creates charts showing topics taught in a course, and how they relate to each other.

## Usage

```
python curriculum_flow_charts.py <topics file> <events file> [args]
```

### topics file

A file containing the topics in the course.
The file should be in tab separated values (tsv) format.
The first line is ignored and may include headers.
Each following line should have a single topic, in this format:

- The first entry is the name of the topic.
- The second entry is a semicolon separated list of dependency topics.
- Any additional entries are ignored.

Example topics table (also found in demo_topics.tsv):

| Topic          |    Dependencies    |                       Description |
|:---------------|:------------------:|----------------------------------:|
| Counting       |                    | How to count items one at a time. |
| Addition       |      Counting      |           Adding counts together. |
| Subtraction    |      Counting      |   Taking counts away from counts. |
| Multiplication | Addition; Counting |                Repeated addition. |

### events file

A file containing the events in the course.
The file should be in tab separated values (tsv) format.
The first line is ignored and may include headers.
Each following line should have a single event, in this format:

- The fist entry is ignored
- The second entry is the name of the event.
- The third entry is a semicolon separated list of topics taught in the event.
- The fourth entry is a semicolon separated list of topics required by the event.

Each event has a type of either <i>lecture</i>, <i>lab</i>, <i>homework</i>, or <i>project</i>.
Each event also has a unit number and group id.
No two events should have the same type, unit, and group.
This information is parsed from the event name, in this manner:

- If the name includes a hyphen, only the part of the name preceding any hyphens is considered.
- The event type is determined by the presence of 'lecture', 'lab', 'homework' (or 'hw'), or 'project' in the event
  name, ignoring casing.
- The unit number is parsed from the first uninterrupted series of digits in the name.
- The group id is the character immediately following the last character of the unit number, if not whitespace.
  A <i>project</i> may omit the group id, if it is the only <i>project</i> in the unit.

Chronological ordering of events is based on the unit number, then group id, then event type.
Event type orderings from first to last are:

1. <i>Lecture</i>
2. <i>Lab</i>
3. <i>Homework</i>
4. <i>Project</i>

Example events table (also found in demo_events.tsv):

| <i>This column is ignored, as well as this row.</i> |             Name             | Topics Taught  |       Topics Required |
|:----------------------------------------------------|:----------------------------:|:--------------:|----------------------:|
|                                                     |    Lecture 1a - Counting     |    Counting    |                       |
|                                                     |      Lab 1a - Counting       |                |              Counting |
|                                                     |       HW 1a - Counting       |                |              Counting |
|                                                     |    Lecture 1b - Addition     |    Addition    |                       |
|                                                     |      Lab 1b - Addition       |                |              Addition |
|                                                     |       HW 1b - Addition       |                |              Addition |
|                                                     |   Lecture 1c - Subtraction   |  Subtraction   |                       |
|                                                     |     Lab 1c - Subtraction     |                |           Subtraction |
|                                                     |  Homework 1c - Subtraction   |                |           Subtraction |
|                                                     | Project 1 - Basic Operations |                | Addition; Subtraction |
|                                                     | Lecture 2a - Multiplication  | Multiplication |                       |
|                                                     |   Lab 2a - Multiplication    |                |        Multiplication |
|                                                     | Homework 2a - Multiplication |                |        Multiplication |

### Topic lists

An additional notes about semicolon separated lists of topics in both the topics file and events file:
<i>Any topic in a list that is a dependency of another topic in that list will be ignored.</i>

### Verifying the topics and events files

To check if your files are well-formed and get feedback on possible errors,
including redundant dependencies/requirements, you can use the following command:

```
python curriculum_flow_charts.py <topics file> <events file> --info-level info
```

# Chart Types

There are several different charts to choose from, and multiple charts can be drawn in a single command.

## Topics

Draws all topics and their dependency relations.

```
python curriculum_flow_charts.py <topics file> <events file> --all-topics
```

## Topics by Event

Draws all topics and their dependency relations, and groups topics into the events they are taught in.

```
python curriculum_flow_charts.py <topics file> <events file> --topics-by-event
```

## Focus Topic

Draws all things related to a specific topic, grouping things by unit, group, and event.
The topic name can be abbreviated if it is unambiguous.

```
python curriculum_flow_charts.py <topics file> <events file> --topic <topic>
```

## Focus Event

Draws all things related to the topics in a specific event, grouping things by unit, group, and event.
The event name can be abbreviated if it is unambiguous.

```
python curriculum_flow_charts.py <topics file> <events file> --event <event>
```

## Full

Draws everything.
Takes significantly longer to process as the course complexity increases.

```
python curriculum_flow_charts.py <topics file> <events file> --full
```

# Additional Options

### `--output-dir <dir>`

Specifies the directory to save the resultant charts to.

### `--output-prefix <prefix>`

Specifies a prefix to prepend resultant filenames with.

### `--debug-rank`

For development purposes only.
Draws extra information about how the chart enforces node ranks.

### `--info-level <info/warning/error/silent>`

Limits the amount of information printed while reading the topics and events files.