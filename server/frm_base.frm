<?xml version="1.0" encoding="UTF-8" ?>
<ENSEMBLE-FORMULE classe="ensemble_formule" nom="frm_base" date-création="2017-06-02" heure-création="17:42:49">
    <objet nom="pers">
        <Producteur nom="pers" seuil_exclusion="8" activer_seuil_exclusion="0" activation="1" active_liste_associee="0" nom_liste_associéee="" Var="N" ressource_associée="" />
        <objet classe="formule" nom='/!P /NOMLISTE=&quot;Prénoms&quot; /!N   /MAJENT' />
        <objet classe="formule" nom='/!P1 /NOMLISTE=&quot;Prénoms&quot; De  /!N   /MAJENT' />
        <objet classe="formule" nom='/!P1 /NOMLISTE=&quot;Prénoms&quot; Le  /!N   /MAJENT' />
    </objet>
   <objet nom="entite_qualite">
        <Producteur nom="entq" seuil_exclusion="8" activer_seuil_exclusion="0" activation="1" active_liste_associee="0" nom_liste_associéee="" Var="E" ressource_associée="" />
        <objet classe="formule" nom="/!E /ENTITE /!Q /QUALITE" />
        <objet classe="formule" nom=" /!E /ENTITE est /!Q /QUALITE" />
    </objet>    
</ENSEMBLE-FORMULE>
