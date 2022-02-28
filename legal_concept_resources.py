# -*- coding: utf-8 -*-
"""
Created on Sat Feb 12 12:13:55 2022

@author: bejob
"""
#%% Label lists
lov_label_list = ['legal_concept','lov']

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
                 
external_reference_cues = [" i lov om"]                 