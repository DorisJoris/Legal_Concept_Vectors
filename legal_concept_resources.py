# -*- coding: utf-8 -*-
"""
Created on Sat Feb 12 12:13:55 2022

@author: bejob
"""
#%% Label lists
hierachical_label_list = ['list','stk','paragraf','chapter','section', 'lov']

lov_label_list = ['legal_concept','lov']

section_label_list = ['legal_concept','section']

chapter_label_list = ['legal_concept','chapter']

paragraph_label_list = ['legal_concept','paragraf']

stk_label_list = ['legal_concept','stk']

litra_label_list = ['legal_concept','list', 'litra']
nr_label_list = ['legal_concept','list', 'number']

sentence_label_list = ['legal_concept', 'sentence']

#%% Abbreviations used in danish laws

abbreviations = [[' alm.', ' alm%%'], [' Alm.', ' Alm%%'],
                 [' ang.', ' ang%%'], [' Ang.', ' Ang%%'],
                 [' art.', ' art%%'], [' Art.', ' Art%%'],
                 [' bl.a.', ' bl%%a%%'], [' Bl.a.', ' Bl%%a%%'],
                 [' ca.', ' ca%%'], [' Ca.', ' Ca%%'],
                 [' d.d.', ' d%%d%%'], [' D.d.', ' D%%d%%'],
                 [' dkr.', ' dkr%%'], [' Dkr.', ' Dkr%%'],
                 [' ds.', ' ds%%'], [' Ds.', ' Ds%%'],
                 [' d.å.', ' d%%å%%'], [' D.å.', ' D%%å%%'],
                 [' dvs.', ' dvs%%'], [' Dvs.', ' Dvs%%'],
                 [' ekskl.', ' ekskl%%'], [' Ekskl.', ' Ekskl%%'],
                 [' el.lign.', ' el%%lign%%'], [' El.lign.', ' El%%lign%%'],
                 [' etc.', ' etc%%'], [' Etc.', ' Etc%%'],
                 [' evt.', ' evt%%'], [' Evt.', ' Evt%%'],
                 [' f.eks.', ' f%%eks%%'], [' F.eks.', ' F%%eks%%'],
                 [' fg.', ' fg%%'], [' Fg.', ' Fg%%'],
                 [' fhv.', ' fhv%%'], [' Fhv.', ' Fhv%%'],
                 [' fmd.', ' fmd%%'], [' Fmd.', ' Fmd%%'],
                 [' ff.', ' ff%%'], [' Ff.', ' Ff%%'],
                 [' f.', ' f%%'], [' F.', ' F%%'],
                 [' flg.', ' flg%%'], [' Flg.', ' Flg%%'],
                 [' hhv.', ' hhv%%'], [' Hhv.', ' Hhv%%'],
                 [' inkl.', ' inkl%%'], [' Inkl.', ' Inkl%%'],
                 [' j.nr.', ' j%%nr%%'], [' J.nr.', ' J%%nr%%'],
                 [' jf.',' jf%%'], [' Jf.',' Jf%%'], 
                 [' kgl.',' kgl%%'],[' kgl.',' kgl%%'],
                 [' kl.', ' kl%%'], [' Kl.', ' Kl%%'],
                 [' kr.', ' kr%%'], [' Kr.', ' Kr%%'],
                 [' lign.', ' lign%%'], [' Lign.', ' Lign%%'],
                 [' maks.', ' maks%%'], [' Maks.', ' Maks%%'],
                 [' mht.', ' mht%%'], [' Mht.', ' Mht%%'],
                 [' md.', ' md%%'], [' Md.', ' Md%%'],
                 [' mdr.', ' mdr%%'], [' Mdr.', ' Mdr%%'],
                 [' mdl.', ' mdl%%'], [' Mdl.', ' Mdl%%'],
                 [' m.fl.', ' m%%fl%%'], [' M.fl.', ' M%%fl%%'],
                 [' m.m.', ' m%%m%%'], [' M.m.', ' M%%m%%'],
                 [' m.v.', ' m%%v%%'], [' M.v.', ' M%%v%%'],
                 [' m.v.,', ' m%%v%%,'],
                 [' mia.', ' mia%%'], [' Mia.', ' Mia%%'],
                 [' mio.', ' mio%%'], [' Mio.', ' Mio%%'],
                 [' nkr.', ' nkr%%'], [' Nkr.', ' Nkr%%'],
                 [' nfmd.', ' nfmd%%'], [' Nfmd.', ' Nfmd%%'],
                 [' nr.',' nr%%'],[' Nr.',' Nr%%'],
                 [' o.lign.',' o%%lign%%'],[' O.lign.',' O%%lign%%'],
                 [' osv.', ' osv%%'], [' Osv.', ' Osv%%'],
                 [' o.k.', ' o%%k%%'], [' O.k.', ' O%%k%%'],
                 [' pga.', ' pga%%'], [' Pga.', ' Pga%%'],
                 [' pr.', ' pr%%'], [' Pr.', ' Pr%%'],
                 [' pct.', ' pct%%'], [' Pct.', ' Pct%%'],
                 [' pkt.', ' pkt%%'], [' Pkt.', ' Pkt%%'],
                 [' p.u.v.', ' p%%u%%v%%'], [' P.u.v.', ' P%%u%%v%%'],
                 [' s.', ' s%%'], [' S.', ' S%%'],
                 [' sek.', ' sek%%'], [' Sek.', ' Sek%%'],
                 [' skr.', ' skr%%'], [' Skr.', ' Skr%%'],
                 [' stk.',' stk%%'], [' Stk.',' Stk%%'],
                 [' td.', ' td%%'], [' Td.', ' Td%%'],
                 [' tdr.', ' tdr%%'], [' Tdr.', ' Tdr%%'],
                 [' vedr.', ' vedr%%'], [' Vedr.', ' Vedr%%']
                 ]

reference_cues = [" bestemmelserne i §", "  betingelserne i §", 
                  " i henhold til"]

relative_stk_ref_cues = [" overtrædelse af disse bestemmelser", 
                         " overtrædelse af denne bestemmelse",
                         " denne paragrafs bestemmelser",
                         " ovennævnte regler"
                         ]


internal_ref_to_whole_law_cues = [" denne lov", " for lovens anvendelse",
                             " denne lovs bestemmelser", " loven",
                             " lovens"
                           ]
                 
external_reference_cues = [(" barselloven", "LBK nr 235 af 12/02/2021"),
                           (" dansk lovgivning om social sikring", ""),
                           (" direktiv nr. 92/85/EØF om iværksættelse af foranstaltninger til forbedring af sikkerheden og sundheden under arbejdet for arbejdstagere", ""),
                           (" EF-forordninger om koordinering af de sociale sikringsordninger", ""),
                           (" ferieloven", ""),
                           (" funktionærloven", "LBK nr 1002 af 24/08/2017"),
                           (" lov om afgift af lønsum m.v.", ""),
                           (" lov om aktiv socialpolitik", ""),
                           (" lov om Arbejdsmarkedets Tillægspension", ""),
                           (" lov om arbejdsløshedsforsikring m.v.", ""),
                           (" lov om brug af køberet eller tegningsret til aktier m.v.", "LOV nr 309 af 05/05/2004"),
                           (" lov om børnetilskud", ""),
                           (" lov om dagpenge ved sygdom eller fødsel", ""),
                           (" lov om en aktiv beskæftigelsesindsats", ""),
                           (" lov om en satsreguleringsprocent", ""),
                           (" lov om et indkomstregister", ""),
                           (" lov om fleksydelse", ""),
                           (" lov om højeste, mellemste, forhøjet almindelig og almindelig førtidspension m.v.", ""),
                           (" lov om ligebehandling af mænd og kvinder med hensyn til beskæftigelse m.v.", ""),
                           (" lov om pas til danske statsborgere m.v.", ""),
                           (" lov om retssikkerhed og administration på det sociale område", ""),
                           (" lov om social pension", ""),
                           (" lov om social service", ""),
                           (" lov om statens voksenuddannelsesstøtte", ""),
                           (" lov om sygedagpenge", ""),
                           (" lov om tidsbegrænset ansættelse", "LBK nr 907 af 11/09/2008"),
                           (" momsloven", ""),
                           (" renteloven", ""),
                           (" SU-loven", ""),
                           (" straffeloven", ""),
                           ]                 