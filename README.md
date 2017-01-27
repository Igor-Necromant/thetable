# thetable
## Intro
Hello,

This is an extended tool for SQLite database creation and management. This program is made for creating an SQLite database from the correctly set up XML module file. The goal is to change databases' details without using SQL and even without any loss of data in cases when you need to change database architecture after it has already been populated with data.

This readme file eventually will contain a guide on how to use all the features implemented in the software, for now I will fill it with short examples.

## Launching the program
This should do the thing if you have all requirements installed:
```
git clone https://github.com/Igor-Necromant/thetable
python thetable/main.py
```
### Requirements
* Python 3.4 or newer
* PyQt4
* SQLite

### It launched, what now?
Unfortunately, "Help" hasn't been implemented as part of the software yet, so for now quick'n'dirty help will be written here.

First you need to open a module, for that you need XML module file. `thetable/example.xml` should be enough for the first launch.

After module is open, the program seeks for a .db file which is obviously not present yet. Push `createDB` button to fix that. This creates a database file based on contents of XML module file. A list of tables appears on the right. Now you can add, delete or edit (double click existing entry).

You can also press `loadDefaults` button to fill all tables with data from `thetable/defaults.xml` (this removes all the current entries). Alternatively you can push `writeAsDefaults` to rewrite `thetable/defaults.xml` with current contents of the table. `writeAllAsDefaults` writes all tables, not just the currently active one.
 
Proceeding with this README file will help you understand how to create your own XML modules and make something useful out of this program =)

## XML module file structure
### Skeleton
To put it simple, it looks like that:
```
<database ...>
    <table ...>
        <field ... />
        ...
    </table>
    ...
</database>
```
Nothing hard with that, there can be only one `database` tag and multiple `table` and `field` tags inside of it.

Let's say I want to make a database for storing my contact list. At a first glance, it will look like that:

```
<database file="contacts.db" name="My contacts">
    <table name="contacts">
        <field name="id" type="pk"/>
        <field name="name" type="line"/>
        <field name="address" type="line"/>
        <field name="description" type="text"/>
    </table>
</database>
```
Now there are attributes added to each tag. What do they mean?

* **database**:
  * *file* - essentially name of the SQL database file.
  * *name* - human-friendly name that will also be window title of `thetable` application when you launch it. This field is not required.
* **table**:
  * *name* - name of the table it wil be referenced by. Table names must be unique.
* **field**:
  * *name* - name of the field it will be referenced by in the future. Within one table names should not repeat.
  * *type* - type of data that will be stored in this field. Three data types were represented in the example: `pk` stands for Primary Key and there must be one and only one such field in every table; `line` means text info; same goes for `text`. Difference between `text` and `line` is about the way it will be graphically displayed. `text` is ready for a couple of paragraphs of information, while `line` is just one line. 

### Referencing other tables

Let's enhance our database and include a phone number for each contact.
```
<field name="phone" type="line"/>
```
Now that is too simple. What if one has contacts from various countries? Each country has different country code and each phone number will be very different. Let's add that to our database and store our phone numbers separately from country codes.

There is no point to create field for country code and fill it for every contact, because if you have two contacts from France, you will have to input the same country code twice. It is much better to create a different table that stores country codes and our `contacts` table will simply reference an entry from `countries` table.

```
<database file="contacts.db" name="My contacts">
    <table name="contacts">
        <field name="id" type="pk"/>
        <field name="name" type="line"/>
        <field name="address" type="line"/>
        <field name="description" type="text"/>
        <field name="country" type="fk" fk="countries"/>
        <field name="phone" type="line"/>
    </table>
    <table name="countries">
        <field name="id" type="pk"/>
        <field name="name" type="line"/>
        <field name="country_phone_code" type="line"/>
    </table>
</database>
```
So `fk` is a new type, it stands for Foreign Key and is a key mechanism in SQL for referencing. We say that `type="fk"` and then using `fk="countries"` we specify what table this key is referencing to.

### Views

If you launch a program now, you will see ugly numbers instead of country names in `country` field. There is a way to change that using views. Here is an example:

```
<table name="contacts">
        <field name="id" type="pk"/>
        <field name="name" type="line"/>
        <field name="address" type="line"/>
        <field name="description" type="text"/>
        <field name="country" type="fk" fk="countries"/>
        <field name="phone" type="line"/>
        <view name="advanced">
            <name/>
            <address/>
            <country.name/>
            <country.country_phone_code>Country code</country.country_phone_code>
            <phone/>
        </view>
    </table>
```
If you launch a program now, on the bottom right you get to select a view and you can choose newly created `advanced` view.

`name` attribute in `view` specifies display name. If it is set to `default`, it overwrites default view.

Tags inside `view` tag should be names of `contacts` fields. If a field's type is `fk` you can use a dot to address a field of the table that fk references too. In this example `country.name` references to the name of the country from `countries` table and same for `country_phone_code`.

Through views you can also change display names of fields. In the given example `country_phone_code` is not very beautiful name for a column, so we rename it to `Country code` and this is what program will show.

Views are also good for omitting irrelevant (for displaying) data like `id` (in some cases) or `description` that can be too long.