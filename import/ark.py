#!/usr/bin/python

import dbfread, asm

"""
Import script for ARK DBF databases, covers people, animals, payments, licences and complaints

21st March, 2015
"""

PATH = "data/arktest"

owners = []
ownerdonations = []
ownerlicences = []
movements = []
animals = []
animalcontrol = []
ppa = {}
ppo = {}

arkspecies = {
    "C": 1, # Dog
    "F": 2, # Cat
    "E": 24 # Horse
}

asm.setid("animal", 100)
asm.setid("owner", 100)
asm.setid("ownerdonation", 100)
asm.setid("ownerlicences", 100)
asm.setid("adoption", 100)
asm.setid("animalcontrol", 100)

print "\\set ON_ERROR_STOP\nBEGIN;"
print "DELETE FROM animal WHERE ID >= 100;"
print "DELETE FROM owner WHERE ID >= 100;"
print "DELETE FROM ownerdonation WHERE ID >= 100;"
print "DELETE FROM adoption WHERE ID >= 100;"

for p in dbfread.read("%s/NAMES.DBF" % PATH):
    o = asm.Owner()
    owners.append(o)
    ppo[p["ID"]] = o
    o.OwnerForeNames = p["F_NAME"]
    o.OwnerSurname = p["L_NAME"]
    o.OwnerAddress = "%s %s\n%s" % (p["ADR_ST_NUM"], p["ADR_ST_NAM"], p["ADR_LINE2"])
    o.OwnerTown = p["CITY"]
    o.OwnerCounty = p["STATE"]
    o.OwnerPostcode = ["ZIP"]
    o.HomeTelephone = p["H_PHONE"]
    o.WorkTelephone = p["W_PHONE"]
    comments = "ID: %s" % p["ID"]
    comments += "\n%s" % asm.nulltostr(p["NAMES_TXT"])
    o.Comments = comments

for d in dbfread.read("%s/ANIMALS.DBF" % PATH):
    a = asm.Animal()
    animals.append(a)
    ppa[d["ID_NUM"]] = a
    a.AnimalName = d["NAME"]
    if d["SPECIES"] == "C":
        # Canine
        a.SpeciesID = 1
        if d["SURR_CODE"] == "STR":
            a.AnimalTypeID = 10
            a.EntryReasonID = 11
        else:
            a.AnimalTypeID = 2
    elif d["SPECIES"] == "F":
        # Feline
        a.SpeciesID = 2
        if d["SURR_CODE"] == "STR":
            a.EntryReasonID = 11
            a.AnimalTypeID = 12
        else:
            a.AnimalTypeID = 11
    if d["SURR_ID"] != "":
        if ppo.has_key(d["SURR_ID"]):
            a.OriginalOwnerID = ppo[d["SURR_ID"]].ID
    a.Sex = asm.getsex_mf(d["SEX"])
    a.BreedID = asm.breed_id_for_name(d["BREED"])
    a.BaseColourID = asm.colour_id_for_name(d["COLOR"])
    a.BreedName = asm.breed_name_for_id(a.BreedID)
    if d["BREED"].find("MIX") != -1:
        a.CrossBreed = 1
        a.Breed2ID = 442
        a.BreedName = asm.breed_name_for_id(a.BreedID) + " / " + asm.breed_name_for_id(a.Breed2ID)
    a.DateBroughtIn = d["DATE_SURR"]
    if a.DateBroughtIn is None: a.DateBroughtIn = asm.now()
    a.NeuteredDate = d["NEUTER_DAT"]
    if a.NeuteredDate is not None:
        a.Neutered = 1
    a.EstimatedDOB = 1
    dob = a.DateBroughtIn
    if d["AGE"] != "":
        if d["AGE"].find("YR") != -1:
            dob = asm.subtract_days(dob, asm.atoi(d["AGE"]) * 365)
        elif d["AGE"].find("M") != -1:
            dob = asm.subtract_days(dob, asm.atoi(d["AGE"]) * 30)
    a.DateOfBirth = dob
    if d["EUTH_USD"] > 0:
        a.PutToSleep = 1
        a.Archived = 1
        a.DeceasedDate = d["DATE_DISPO"]
    comments = "Original breed: %s\nColor: %s" % (d["BREED"], d["COLOR"])
    a.HiddenAnimalDetals = asm.nulltostr(d["ANIMAL_TXT"])
    a.HealthProblems = d["HEALTH"]
    a.LastChangedDate = a.DateBroughtIn
    if d["ADPT_ID"] != "":
        if ppo.has_key(d["ADPT_ID"]):
            o = ppo[d["ADPT_ID"]]
            m = asm.Movement()
            movements.append(m)
            m.AnimalID = a.ID
            m.OwnerID = o.ID
            m.MovementType = 1
            if d["RECLAIMED"] == "X": 
                m.MovementType = 5
            m.LastChangedDate = m.MovementDate
            a.Archived = 1
            a.ActiveMovementType = m.MovementType
            a.ActiveMovementDate = m.MovementDate

for p in dbfread.read("%s/PAYMENTS.DBF" % PATH):
    od = asm.OwnerDonation()
    ownerdonations.append(od)
    if ppo.has_key(p["PMNT_ID"]):
        o = ppo[p["PMNT_ID"]]
        od.OwnerID = o.ID
        od.Donation = int(p["AMOUNT"] * 100)
        od.Date = p["PMNT_DATE"]
        od.DonationTypeID = 4 # Surrender
        if p["PMNT_CODE"] == "ADP":
            od.DonationTypeID = 2

for l in dbfread.read("%s/LICENSE.DBF" % PATH):
    ol = asm.OwnerLicence()
    ownerlicences.append(ol)
    if ppo.has_key(l["OWNER_ID"]):
        o = ppo[l["OWNER_ID"]]
        ol.OwnerID = o.ID
        ol.LicenceTypeID = 1
        ol.LicenceNumber = l["LIC_NUM"]
        ol.LicenceFee = int(l["FEE"] * 100)
        ol.IssueDate = asm.parse_date("2006-01-01", "%Y-%m-%d")
        ol.ExpiryDate= asm.parse_date("2007-01-01", "%Y-%m-%d")

for c in dbfread.read("%s/CMPLAINT.DBF" % PATH):
    ac = asm.AnimalControl()
    animalcontrol.append(ac)
    if c["FROM_ID"] != "" and ppo.has_key(c["FROM_ID"]):
        ac.CallerID = ppo[c["FROM_ID"]].ID
    if c["ABOUT_ID"] != "" and ppo.has_key(c["ABOUT_ID"]):
        ac.OwnerID = ppo[c["ABOUT_ID"]].ID
    ac.CallDateTime = c["C_DATE"]
    ac.IncidentDateTime = ac.CallDateTime
    ac.DispatchDateTime = ac.CallDateTime
    ac.CompletedDate = ac.CallDateTime
    ac.DispatchAddress = c["C_LOCATION"]
    if arkspecies.has_key(c["C_SPECIES"]):
        ac.SpeciesID = arkspecies[c["C_SPECIES"]]
    ac.Sex = asm.getsex_mf(c["C_SEX"])
    comments = ""
    comments = "Problem: %s" % c["PROBLEM"]
    if c["FOLLOW_UP"] != "": comments += "\nFollowup: %s" % c["FOLLOW_UP"]
    if c["OFFICER_ID"] != "": comments += "\nOfficer: %s" % c["OFFICER_ID"]
    if c["CITATION"] != "": comments += "\nCitation: %s" % c["CITATION"]
    if c["CMPL_TEXT"] != "": comments += "\nCompleted: %s" % c["CMPL_TEXT"]
    ac.CallNotes = comments

for a in animals:
    print a
for o in owners:
    print o
for m in movements:
    print m
for od in ownerdonations:
    print od
for ol in ownerlicences:
    print ol
for ac in animalcontrol:
    print ac

print "DELETE FROM configuration WHERE ItemName LIKE 'DBView%';"
print "COMMIT;"
