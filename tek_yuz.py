"""FaceFusion yamasi — Docker derlemesinde calisir (ff-worker Dockerfile).

Sorun (2026-10-11): "reference" modunda FaceFusion, referans yuze (sablondaki
kahraman) esikten daha cok benzeyen HER yuzu degistiriyor. Yapay zeka
videolarinda figuranlar kahramana benzedigi icin sahnedeki herkes kullanicinin
yuzunu aliyordu (ornek: Guverte Dovusu, esik 0.4'te bile 3 kisi).

Yama: OS_SINGLE_FACE=1 ortam degiskeni varsa her karede yalniz kahramana EN
cok benzeyen TEK yuz doner. Degisken yoksa FaceFusion birebir eski davranir.
Handler bu degiskeni is girdisindeki single_face ile acar.
"""
P = '/facefusion/facefusion/face_selector.py'
s = open(P).read()

OLD = (
    "\t\t\tmatch_faces = find_match_faces([ reference_face ], target_faces, "
    "state_manager.get_item('reference_face_distance'))\n"
    "\t\t\treturn match_faces\n"
)
NEW = (
    "\t\t\tmatch_faces = find_match_faces([ reference_face ], target_faces, "
    "state_manager.get_item('reference_face_distance'))\n"
    "\t\t\tif match_faces and __import__('os').environ.get('OS_SINGLE_FACE') == '1':\n"
    "\t\t\t\treturn [ min(match_faces, key = lambda face: calculate_face_distance(face, reference_face)) ]\n"
    "\t\t\treturn match_faces\n"
)
if s.count(OLD) != 1:
    raise SystemExit('tek_yuz.py: face_selector.py beklenen bicimde degil '
                     '(FaceFusion surumu degismis olabilir) — yama UYGULANMADI')
open(P, 'w').write(s.replace(OLD, NEW))
print('tek_yuz.py: face_selector.py yamalandi (OS_SINGLE_FACE)')
