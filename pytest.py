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
# Functions useful for the testing in __main__.
def testFlags(steerer, cone_sizes=None, pt_cuts=None):
    if not cone_sizes:
        cone_sizes = ["0.00", "0.04","0.08", "0.12", "0.16", "0.20", "0.30"]
    if not pt_cuts:
        pt_cuts = ["0.0", "0.5", "1.0", "2.0"]
    def tauConesDict(flag, cone_size, pt_cut):
        return {
            "IsolationConeAngle": dict(value="0.32"),
            "MaxCosTheta": dict(value="1.1"),
            "MinPtSeed": dict(value="2.0"),
            "OutputRootFile": dict(value=f"flag={flag}_cone={cone_size}"
              "_pt_cut={pt_cut}_tau_cones_bdt_input"),
            "PtCut": dict(value=pt_cut),
            "SearchConeAngle": dict(value=cone_size),
            "TauFlag": dict(value=str(flag)),
        }
    processor = "TauConesBDTInputProcessor"
    for flag in range(32):
        for cone_size in cone_sizes:
            pt_cut = "0.0"
            steerer.add(processor, tauConesDict(flag, cone_size, pt_cut))
        for pt_cut in pt_cuts:
            cone_size = "0.08"
            steerer.add(processor, tauConesDict(flag, cone_size, pt_cut))
    return steerer

def tauChain(steerer):
    steerer.add("TauConesProcessor", {
        "IsolationConeAngle": dict(value="0.30"),
        "SearchConeAngle": dict(value="0.13"),
        "MaxCosTheta": dict(value="1.1"),
        "MinPtSeed": dict(value="3.0"),
        "PtCut": dict(value="1.0"),
    })
    steerer.add("IsolatedLeptonTaggingProcessor")
    for dec_channel in ["ZDec_TAU"]: # ["ZDec_EL", "ZDec_MU", "ZDec_TAU", "ZDec_NU"]:
        steerer.add("SplitOffZProcessor", {
            "ZDecayChannel": dict(value=dec_channel),
            "HiggsCollection": dict(value="HRemnantsPFOs_{}".format(dec_channel)),
            "ZCollection": dict(value="ZRemnantsPFOs_{}".format(dec_channel)),
            "OverlayCollection": dict(value="OverlayPFOs_{}".format(dec_channel)),
    })
    return steerer

# ------------------------------------------------------------------------------
# Some basic test/use examples for pysteer.
if __name__ == "__main__":
    steerer = Pysteer(change_parameter_defaults=cpd,
        set_parameter_value={"EncodingStringParameterName": "stringper"},
        local_project_paths=["/home/kunath/iLCSoft/projects/reference-sample"],
    )
    steerer.marlin_global.Verbosity = "DEBUG"
    steerer.marlin_global.MaxRecordNumber = -1#2000 #000

    #testFlags(steerer)
    tauChain(steerer)

    steerer.write(xml_name="tmp/steer.xml")
    #print(steerer)
    steerer.run(batch_mode=False)
    #steerer.run(batch_mode=False, pols=["eLpL"], debug_process="Pe1e1h")
