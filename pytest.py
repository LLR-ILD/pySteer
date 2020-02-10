from pysteer import Pysteer

# ------------------------------------------------------------------------------
# Parameter defaults in this project.
cpd = {"IsolatedLeptonTaggingProcessor": {
    "DirOfISOElectronWeights": {"value":
        "/cvmfs/ilc.desy.de/sw/x86_64_gcc49_sl6/v02-00-02/MarlinReco/v01-25/Analysis/IsolatedLeptonTagging/weights/e1e1h_gg_qqqq_250"},
    "DirOfISOMuonWeights": {"value":
        "/cvmfs/ilc.desy.de/sw/x86_64_gcc49_sl6/v02-00-02/MarlinReco/v01-25/Analysis/IsolatedLeptonTagging/weights/yyxylv_yyxyyx_woYoke_500.mILD_l5_o1_v02"},
    },
}

# ------------------------------------------------------------------------------
# Some basic test/use examples for pysteer.
if __name__ == "__main__":
    steerer = Pysteer(change_parameter_defaults=cpd,
        set_parameter_value={"EncodingStringParameterName": "stringper"})
    steerer.add("TauConesProcessor", {"IsolationConeAngle": dict(value=".3")})
    steerer.add("IsolatedLeptonTaggingProcessor")
    #steerer.write(xml_name="steer.xml")
    #print(steerer)
    steerer.marlin_global.MaxRecordNumber = 5000
    steerer.run()
