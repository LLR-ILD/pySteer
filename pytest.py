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
    steerer.marlin_global.Verbosity = "DEBUG"
    #steerer.add("TauFromTrackProcessor")
    #steerer.add("TauConesProcessor",{
    #    "IsolationConeAngle": dict(value=".3"),
    #    "IsolationEnergy": dict(value="1.5"),
    #    "MaxInvariantMass": dict(value="2.0"),
    #    "SearchConeAngle": dict(value=".12")
    #})


    #for min_pt_seed in ["1.5"]:#["0.0", "1.0", "1.5", "2.0", "3.0", "4.0", "5.0", "7.5", "10."]:
    #    steerer.add("TauConesBDTInputProcessor", {
    #        "IsolationConeAngle": dict(value="0.2"),
    #        "MaxCosTheta": dict(value="1.1"),#"0.99"),
    #        "MinPtSeed": dict(value=min_pt_seed),#"1.0"),
    #        "OutputRootFile": dict(value=f"{min_pt_seed}tau_cones_bdt_input"),
    #        "PtCut": dict(value="0.0"),#"0.2"),
    #        "SearchConeAngle": dict(value="0.15"),#"0.1"),
    #    })

    steerer.add("DraftProcessor")

    #steerer.add("IsolatedLeptonTaggingProcessor")
    #for dec_channel in ["ZDec_EL", "ZDec_MU", "ZDec_TAU", "ZDec_NU"]:
    #    steerer.add("SplitOffZProcessor", {
    #        "ZDecayChannel": dict(value=dec_channel),
    #        "HiggsCollection": dict(value="HRemnantsPFOs_{}".format(dec_channel)),
    #        "ZCollection": dict(value="ZRemnantsPFOs_{}".format(dec_channel)),
    #        "OverlayCollection": dict(value="OverlayPFOs_{}".format(dec_channel)),
    #    })
    #steerer.write(xml_name="steer.xml")
    #print(steerer)
    steerer.marlin_global.MaxRecordNumber = 100 #000
    steerer.run(batch_mode=False)
    #steerer.run(batch_mode=False, pols=["eLpL"], debug_process="Pe1e1h")
