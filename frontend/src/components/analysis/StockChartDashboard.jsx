import React, { useState, useEffect, useRef } from 'react';
import StockChart from './StockChart';

const StockChartDashboard = () => {
  const [selectedTicker, setSelectedTicker] = useState('AAPL'); // Default to AAPL
  const [searchTerm, setSearchTerm] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const searchRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Complete list of NASDAQ stocks from the CSV file
  const tickers = [
    { value: 'AAPL', label: 'Apple Inc. (AAPL)' },
    { value: 'ABNB', label: 'Airbnb Inc. (ABNB)' },
    { value: 'ADBE', label: 'Adobe Inc. (ADBE)' },
    { value: 'ADI', label: 'Analog Devices Inc. (ADI)' },
    { value: 'ADP', label: 'Automatic Data Processing Inc. (ADP)' },
    { value: 'ADSK', label: 'Autodesk Inc. (ADSK)' },
    { value: 'AEP', label: 'American Electric Power Company Inc. (AEP)' },
    { value: 'AFRM', label: 'Affirm Holdings Inc. (AFRM)' },
    { value: 'AGNC', label: 'AGNC Investment Corp. (AGNC)' },
    { value: 'AKAM', label: 'Akamai Technologies Inc. (AKAM)' },
    { value: 'ALAB', label: 'Astera Labs Inc. (ALAB)' },
    { value: 'ALGN', label: 'Align Technology Inc. (ALGN)' },
    { value: 'ALNY', label: 'Alnylam Pharmaceuticals Inc. (ALNY)' },
    { value: 'AMAT', label: 'Applied Materials Inc. (AMAT)' },
    { value: 'AMD', label: 'Advanced Micro Devices Inc. (AMD)' },
    { value: 'AMGN', label: 'Amgen Inc. (AMGN)' },
    { value: 'AMZN', label: 'Amazon.com Inc. (AMZN)' },
    { value: 'APP', label: 'Applovin Corporation (APP)' },
    { value: 'ARCC', label: 'Ares Capital Corporation (ARCC)' },
    { value: 'ASTS', label: 'AST SpaceMobile Inc. (ASTS)' },
    { value: 'AUR', label: 'Aurora Innovation Inc. (AUR)' },
    { value: 'AVAV', label: 'AeroVironment Inc. (AVAV)' },
    { value: 'AVGO', label: 'Broadcom Inc. (AVGO)' },
    { value: 'AXON', label: 'Axon Enterprise Inc. (AXON)' },
    { value: 'BIIB', label: 'Biogen Inc. (BIIB)' },
    { value: 'BKNG', label: 'Booking Holdings Inc. (BKNG)' },
    { value: 'BKR', label: 'Baker Hughes Company (BKR)' },
    { value: 'BMRN', label: 'BioMarin Pharmaceutical Inc. (BMRN)' },
    { value: 'BSY', label: 'Bentley Systems Incorporated (BSY)' },
    { value: 'CAI', label: 'Caris Life Sciences Inc. (CAI)' },
    { value: 'CART', label: 'Maplebear Inc. (CART)' },
    { value: 'CASY', label: 'Casey\'s General Stores Inc. (CASY)' },
    { value: 'CDNS', label: 'Cadence Design Systems Inc. (CDNS)' },
    { value: 'CDW', label: 'CDW Corporation (CDW)' },
    { value: 'CEG', label: 'Constellation Energy Corporation (CEG)' },
    { value: 'CELH', label: 'Celsius Holdings Inc. (CELH)' },
    { value: 'CG', label: 'The Carlyle Group Inc. (CG)' },
    { value: 'CHRW', label: 'C.H. Robinson Worldwide Inc. (CHRW)' },
    { value: 'CHTR', label: 'Charter Communications Inc. (CHTR)' },
    { value: 'CINF', label: 'Cincinnati Financial Corporation (CINF)' },
    { value: 'CMCSA', label: 'Comcast Corporation (CMCSA)' },
    { value: 'CME', label: 'CME Group Inc. (CME)' },
    { value: 'COIN', label: 'Coinbase Global Inc. (COIN)' },
    { value: 'COKE', label: 'Coca-Cola Consolidated Inc. (COKE)' },
    { value: 'COO', label: 'The Cooper Companies Inc. (COO)' },
    { value: 'COOP', label: 'Mr. Cooper Group Inc. (COOP)' },
    { value: 'COST', label: 'Costco Wholesale Corporation (COST)' },
    { value: 'CPRT', label: 'Copart Inc. (CPRT)' },
    { value: 'CRDO', label: 'Credo Technology Group Holding Ltd (CRDO)' },
    { value: 'CRWD', label: 'CrowdStrike Holdings Inc. (CRWD)' },
    { value: 'CSCO', label: 'Cisco Systems Inc. (CSCO)' },
    { value: 'CSGP', label: 'CoStar Group Inc. (CSGP)' },
    { value: 'CSX', label: 'CSX Corporation (CSX)' },
    { value: 'CTAS', label: 'Cintas Corporation (CTAS)' },
    { value: 'CTSH', label: 'Cognizant Technology Solutions Corporation (CTSH)' },
    { value: 'DASH', label: 'DoorDash Inc. (DASH)' },
    { value: 'DDOG', label: 'Datadog Inc. (DDOG)' },
    { value: 'DKNG', label: 'DraftKings Inc. (DKNG)' },
    { value: 'DLTR', label: 'Dollar Tree Inc. (DLTR)' },
    { value: 'DOCU', label: 'DocuSign Inc. (DOCU)' },
    { value: 'DPZ', label: 'Domino\'s Pizza Inc (DPZ)' },
    { value: 'DUOL', label: 'Duolingo Inc. (DUOL)' },
    { value: 'DXCM', label: 'DexCom Inc. (DXCM)' },
    { value: 'EA', label: 'Electronic Arts Inc. (EA)' },
    { value: 'EBAY', label: 'eBay Inc. (EBAY)' },
    { value: 'ENTG', label: 'Entegris Inc. (ENTG)' },
    { value: 'EQIX', label: 'Equinix Inc. (EQIX)' },
    { value: 'ERIE', label: 'Erie Indemnity Company (ERIE)' },
    { value: 'EVRG', label: 'Evergy Inc. (EVRG)' },
    { value: 'EWBC', label: 'East West Bancorp Inc. (EWBC)' },
    { value: 'EXC', label: 'Exelon Corporation (EXC)' },
    { value: 'EXE', label: 'Expand Energy Corporation (EXE)' },
    { value: 'EXEL', label: 'Exelixis Inc. (EXEL)' },
    { value: 'EXPE', label: 'Expedia Group Inc. (EXPE)' },
    { value: 'FANG', label: 'Diamondback Energy Inc. (FANG)' },
    { value: 'FAST', label: 'Fastenal Company (FAST)' },
    { value: 'FCNCA', label: 'First Citizens BancShares Inc. (FCNCA)' },
    { value: 'FFIV', label: 'F5 Inc. (FFIV)' },
    { value: 'FITB', label: 'Fifth Third Bancorp (FITB)' },
    { value: 'FOX', label: 'Fox Corporation (FOX)' },
    { value: 'FOXA', label: 'Fox Corporation (FOXA)' },
    { value: 'FSLR', label: 'First Solar Inc. (FSLR)' },
    { value: 'FTAI', label: 'FTAI Aviation Ltd. (FTAI)' },
    { value: 'FTNT', label: 'Fortinet Inc. (FTNT)' },
    { value: 'GEHC', label: 'GE HealthCare Technologies Inc. (GEHC)' },
    { value: 'GEN', label: 'Gen Digital Inc. (GEN)' },
    { value: 'GFS', label: 'GlobalFoundries Inc. (GFS)' },
    { value: 'GILD', label: 'Gilead Sciences Inc. (GILD)' },
    { value: 'GLPI', label: 'Gaming and Leisure Properties Inc. (GLPI)' },
    { value: 'GOOG', label: 'Alphabet Inc. Class C (GOOG)' },
    { value: 'GOOGL', label: 'Alphabet Inc. Class A (GOOGL)' },
    { value: 'HAS', label: 'Hasbro Inc. (HAS)' },
    { value: 'HBAN', label: 'Huntington Bancshares Incorporated (HBAN)' },
    { value: 'HOLX', label: 'Hologic Inc. (HOLX)' },
    { value: 'HON', label: 'Honeywell International Inc. (HON)' },
    { value: 'HOOD', label: 'Robinhood Markets Inc. (HOOD)' },
    { value: 'HST', label: 'Host Hotels & Resorts Inc. (HST)' },
    { value: 'IBKR', label: 'Interactive Brokers Group Inc. (IBKR)' },
    { value: 'IDXX', label: 'IDEXX Laboratories Inc. (IDXX)' },
    { value: 'ILMN', label: 'Illumina Inc. (ILMN)' },
    { value: 'INCY', label: 'Incyte Corp. (INCY)' },
    { value: 'INSM', label: 'Insmed Incorporated (INSM)' },
    { value: 'INTC', label: 'Intel Corporation (INTC)' },
    { value: 'INTU', label: 'Intuit Inc. (INTU)' },
    { value: 'ISRG', label: 'Intuitive Surgical Inc. (ISRG)' },
    { value: 'JBHT', label: 'J.B. Hunt Transport Services Inc. (JBHT)' },
    { value: 'JKHY', label: 'Jack Henry & Associates Inc. (JKHY)' },
    { value: 'KDP', label: 'Keurig Dr Pepper Inc. (KDP)' },
    { value: 'KHC', label: 'The Kraft Heinz Company (KHC)' },
    { value: 'KLAC', label: 'KLA Corporation (KLAC)' },
    { value: 'KMB', label: 'Kimberly-Clark Corporation (KMB)' },
    { value: 'KTOS', label: 'Kratos Defense & Security Solutions Inc. (KTOS)' },
    { value: 'LAMR', label: 'Lamar Advertising Company (LAMR)' },
    { value: 'LECO', label: 'Lincoln Electric Holdings Inc. (LECO)' },
    { value: 'LIN', label: 'Linde plc (LIN)' },
    { value: 'LNT', label: 'Alliant Energy Corporation (LNT)' },
    { value: 'LOGI', label: 'Logitech International S.A. (LOGI)' },
    { value: 'LPLA', label: 'LPL Financial Holdings Inc. (LPLA)' },
    { value: 'LRCX', label: 'Lam Research Corporation (LRCX)' },
    { value: 'MANH', label: 'Manhattan Associates Inc. (MANH)' },
    { value: 'MAR', label: 'Marriott International (MAR)' },
    { value: 'MCHP', label: 'Microchip Technology Incorporated (MCHP)' },
    { value: 'MDB', label: 'MongoDB Inc. (MDB)' },
    { value: 'MDLZ', label: 'Mondelez International Inc. (MDLZ)' },
    { value: 'MEDP', label: 'Medpace Holdings Inc. (MEDP)' },
    { value: 'META', label: 'Meta Platforms Inc. (META)' },
    { value: 'MNST', label: 'Monster Beverage Corporation (MNST)' },
    { value: 'MORN', label: 'Morningstar Inc. (MORN)' },
    { value: 'MPWR', label: 'Monolithic Power Systems Inc. (MPWR)' },
    { value: 'MRVL', label: 'Marvell Technology Inc. (MRVL)' },
    { value: 'MSFT', label: 'Microsoft Corporation (MSFT)' },
    { value: 'MSTR', label: 'MicroStrategy Inc (MSTR)' },
    { value: 'MU', label: 'Micron Technology Inc. (MU)' },
    { value: 'NBIX', label: 'Neurocrine Biosciences Inc. (NBIX)' },
    { value: 'NDAQ', label: 'Nasdaq Inc. (NDAQ)' },
    { value: 'NDSN', label: 'Nordson Corporation (NDSN)' },
    { value: 'NFLX', label: 'Netflix Inc. (NFLX)' },
    { value: 'NTAP', label: 'NetApp Inc. (NTAP)' },
    { value: 'NTNX', label: 'Nutanix Inc. (NTNX)' },
    { value: 'NTRA', label: 'Natera Inc. (NTRA)' },
    { value: 'NTRS', label: 'Northern Trust Corporation (NTRS)' },
    { value: 'NVDA', label: 'NVIDIA Corporation (NVDA)' },
    { value: 'NWS', label: 'News Corporation (NWS)' },
    { value: 'NWSA', label: 'News Corporation (NWSA)' },
    { value: 'ODFL', label: 'Old Dominion Freight Line Inc. (ODFL)' },
    { value: 'OKTA', label: 'Okta Inc. (OKTA)' },
    { value: 'ON', label: 'ON Semiconductor Corporation (ON)' },
    { value: 'ORLY', label: 'O\'Reilly Automotive Inc. (ORLY)' },
    { value: 'PAA', label: 'Plains All American Pipeline L.P. (PAA)' },
    { value: 'PANW', label: 'Palo Alto Networks Inc. (PANW)' },
    { value: 'PAYX', label: 'Paychex Inc. (PAYX)' },
    { value: 'PCAR', label: 'PACCAR Inc. (PCAR)' },
    { value: 'PEP', label: 'PepsiCo Inc. (PEP)' },
    { value: 'PFG', label: 'Principal Financial Group Inc (PFG)' },
    { value: 'PLTR', label: 'Palantir Technologies Inc. (PLTR)' },
    { value: 'PODD', label: 'Insulet Corporation (PODD)' },
    { value: 'POOL', label: 'Pool Corporation (POOL)' },
    { value: 'PPC', label: 'Pilgrim\'s Pride Corporation (PPC)' },
    { value: 'PTC', label: 'PTC Inc. (PTC)' },
    { value: 'PYPL', label: 'PayPal Holdings Inc. (PYPL)' },
    { value: 'QCOM', label: 'QUALCOMM Incorporated (QCOM)' },
    { value: 'REG', label: 'Regency Centers Corporation (REG)' },
    { value: 'REGN', label: 'Regeneron Pharmaceuticals Inc. (REGN)' },
    { value: 'RGLD', label: 'Royal Gold Inc. (RGLD)' },
    { value: 'RIVN', label: 'Rivian Automotive Inc. (RIVN)' },
    { value: 'RKLB', label: 'Rocket Lab Corporation (RKLB)' },
    { value: 'ROKU', label: 'Roku Inc. (ROKU)' },
    { value: 'ROP', label: 'Roper Technologies Inc. (ROP)' },
    { value: 'ROST', label: 'Ross Stores Inc. (ROST)' },
    { value: 'RPRX', label: 'Royalty Pharma plc (RPRX)' },
    { value: 'SATS', label: 'EchoStar Corporation (SATS)' },
    { value: 'SBAC', label: 'SBA Communications Corporation (SBAC)' },
    { value: 'SBUX', label: 'Starbucks Corporation (SBUX)' },
    { value: 'SEIC', label: 'SEI Investments Company (SEIC)' },
    { value: 'SFM', label: 'Sprouts Farmers Market Inc. (SFM)' },
    { value: 'SMCI', label: 'Super Micro Computer Inc. (SMCI)' },
    { value: 'SNPS', label: 'Synopsys Inc. (SNPS)' },
    { value: 'SOFI', label: 'SoFi Technologies Inc. (SOFI)' },
    { value: 'SSNC', label: 'SS&C Technologies Holdings Inc. (SSNC)' },
    { value: 'STLD', label: 'Steel Dynamics Inc. (STLD)' },
    { value: 'SWKS', label: 'Skyworks Solutions Inc. (SWKS)' },
    { value: 'SYM', label: 'Symbotic Inc. (SYM)' },
    { value: 'TEM', label: 'Tempus AI Inc. (TEM)' },
    { value: 'TER', label: 'Teradyne Inc. (TER)' },
    { value: 'TLN', label: 'Talen Energy Corporation (TLN)' },
    { value: 'TMUS', label: 'T-Mobile US Inc. (TMUS)' },
    { value: 'TPG', label: 'TPG Inc. (TPG)' },
    { value: 'TRI', label: 'Thomson Reuters Corporation (TRI)' },
    { value: 'TRMB', label: 'Trimble Inc. (TRMB)' },
    { value: 'TROW', label: 'T. Rowe Price Group Inc. (TROW)' },
    { value: 'TSCO', label: 'Tractor Supply Company (TSCO)' },
    { value: 'TSLA', label: 'Tesla Inc. (TSLA)' },
    { value: 'TTD', label: 'The Trade Desk Inc. (TTD)' },
    { value: 'TTWO', label: 'Take-Two Interactive Software Inc. (TTWO)' },
    { value: 'TW', label: 'Tradeweb Markets Inc. (TW)' },
    { value: 'TXN', label: 'Texas Instruments Incorporated (TXN)' },
    { value: 'TXRH', label: 'Texas Roadhouse Inc. (TXRH)' },
    { value: 'UAL', label: 'United Airlines Holdings Inc. (UAL)' },
    { value: 'ULTA', label: 'Ulta Beauty Inc. (ULTA)' },
    { value: 'UTHR', label: 'United Therapeutics Corporation (UTHR)' },
    { value: 'VNOM', label: 'Viper Energy Inc. (VNOM)' },
    { value: 'VRSK', label: 'Verisk Analytics Inc. (VRSK)' },
    { value: 'VRSN', label: 'VeriSign Inc. (VRSN)' },
    { value: 'VRTX', label: 'Vertex Pharmaceuticals Incorporated (VRTX)' },
    { value: 'VTRS', label: 'Viatris Inc. (VTRS)' },
    { value: 'WBD', label: 'Warner Bros. Discovery Inc. (WBD)' },
    { value: 'WDAY', label: 'Workday Inc. (WDAY)' },
    { value: 'WDC', label: 'Western Digital Corporation (WDC)' },
    { value: 'WMG', label: 'Warner Music Group Corp. (WMG)' },
    { value: 'WWD', label: 'Woodward Inc. (WWD)' },
    { value: 'WYNN', label: 'Wynn Resorts Limited (WYNN)' },
    { value: 'XEL', label: 'Xcel Energy Inc. (XEL)' },
    { value: 'Z', label: 'Zillow Group Inc. Class C (Z)' },
    { value: 'ZBRA', label: 'Zebra Technologies Corporation (ZBRA)' },
    { value: 'ZG', label: 'Zillow Group Inc. Class A (ZG)' },
    { value: 'ZM', label: 'Zoom Communications Inc. (ZM)' },
    { value: 'ZS', label: 'Zscaler Inc. (ZS)' }
  ];

  const handleTickerChange = (event) => {
    setSelectedTicker(event.target.value);
  };

  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
    setIsDropdownOpen(true);
  };

  const handleTickerSelect = (ticker) => {
    setSelectedTicker(ticker);
    setSearchTerm('');
    setIsDropdownOpen(false);
  };

  // Filter tickers based on search term
  const filteredTickers = tickers.filter(ticker =>
    ticker.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
    ticker.value.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get the label for the selected ticker
  const selectedTickerLabel = tickers.find(t => t.value === selectedTicker)?.label || selectedTicker;

  return (
    <div className="bg-black border border-white rounded-lg p-6 h-fit">
      <div className="mb-6">
        <div className="mb-4">
        
          
          {/* Search Input */}
          <div className="relative" ref={searchRef}>
            <input
              id="ticker-search"
              type="text"
              value={searchTerm}
              onChange={handleSearchChange}
              onFocus={() => setIsDropdownOpen(true)}
              placeholder={`Search stocks..`}
              className="w-full px-4 py-3 bg-gray-800 border border-white/30 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            
            {/* Search Icon */}
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/50">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            
            {/* Dropdown Results */}
            {isDropdownOpen && searchTerm && (
              <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-white/30 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                {filteredTickers.length > 0 ? (
                  filteredTickers.slice(0, 10).map((ticker) => (
                    <button
                      key={ticker.value}
                      onClick={() => handleTickerSelect(ticker.value)}
                      className="w-full px-4 py-2 text-left text-white hover:bg-gray-700 focus:bg-gray-700 focus:outline-none first:rounded-t-lg last:rounded-b-lg"
                    >
                      <span className="font-medium text-blue-400">{ticker.value}</span>
                      <span className="text-white/70 ml-2">- {ticker.label.split('(')[0].trim()}</span>
                    </button>
                  ))
                ) : (
                  <div className="px-4 py-2 text-white/50">
                    No stocks found matching "{searchTerm}"
                  </div>
                )}
              </div>
            )}
          </div>
          
          
        </div>

       
      </div>

      {/* Stock Chart Component */}
      <StockChart ticker={selectedTicker} />
    </div>
  );
};

export default StockChartDashboard;