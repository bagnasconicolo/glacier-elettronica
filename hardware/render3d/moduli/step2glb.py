# -*- coding: utf-8 -*-
"""STEP (con i colori) -> glTF binario per il visualizzatore three.js.
    python3 step2glb.py ingresso.step uscita.glb"""
import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString, TCollection_AsciiString
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.RWGltf import RWGltf_CafWriter
from OCP.OCP.collections import IndexedDataMap_TCollection_AsciiString_TCollection_AsciiString as InfoMap
from OCP.Message import Message_ProgressRange
from OCP.RWMesh import RWMesh_CoordinateSystem

src, dst = sys.argv[1], sys.argv[2]
doc = TDocStd_Document(TCollection_ExtendedString("MDTV-XCAF"))
r = STEPCAFControl_Reader()
r.SetColorMode(True)
r.SetNameMode(True)
assert r.ReadFile(src) == 1, "lettura STEP fallita"
r.Transfer(doc)
# le forme del documento condividono la geometria con quelle del lettore: meshare queste basta
BRepMesh_IncrementalMesh(r.Reader().OneShape(), 0.05, False, 0.3, True)
w = RWGltf_CafWriter(TCollection_AsciiString(dst), True)
w.ChangeCoordinateSystemConverter().SetInputCoordinateSystem(RWMesh_CoordinateSystem.RWMesh_CoordinateSystem_Zup)
w.ChangeCoordinateSystemConverter().SetInputLengthUnit(0.001)
w.Perform(doc, InfoMap(), Message_ProgressRange())
print("scritto", dst)
