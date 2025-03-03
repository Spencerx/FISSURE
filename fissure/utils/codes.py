# Message code mappings for low-throughput messaging
MESSAGE_CODE_MAP = {
    "A1": "recallInfoMeshtasticLT",
    "A2": "recallInfoMeshtasticReturnLT",
    "B1": "recallHardwareMeshtasticLT",
    "B2": "recallHardwareMeshtasticReturnLT",
    "C1": "recallStatusMeshtasticLT",
    "C2": "recallStatusMeshtasticReturnLT",    
    "D1": "findGPS_CoordinatesLT",    
    "D2": "findGPS_CoordinatesResultsLT",
    "E1": "scanHardwareLT",    
    "E2": "hardwareScanResultsLT", 
    "F1": "probeHardwareLT",    
    "F2": "hardwareProbeResultsLT", 
}

# Reverse mapping for sending messages
MESSAGE_NAME_TO_CODE = {v: k for k, v in MESSAGE_CODE_MAP.items()}