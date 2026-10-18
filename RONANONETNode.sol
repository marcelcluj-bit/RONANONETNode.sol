// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title RO-NANO-NET Node & Proof-of-Audit Contract
 * @dev Decentralized Physical Infrastructure Network (DePIN) for nanostructural audit.
 * Manages FE-SEM electron microscopy node tokenization, audit records, and automated revenue sharing.
 */

interface IERC20 {
    function transfer(address recipient, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract RONANONETNode {
    string public nodeName;
    string public nodeLocation;
    address public immutable owner;

    uint256 public totalShares;
    mapping(address => uint256) public shares;
    address[] public shareholders;

    struct AuditRecord {
        bytes32 sampleHash;      // Anonymized sample data hash (SHA-256)
        string analysisType;     // Analysis category (e.g., EDS, EBSD, GSR, Microplastics)
        uint256 timestamp;       // Scan timestamp
        uint256 feePaid;         // Fee paid for the audit
    }

    AuditRecord[] public auditHistory;
    uint256 public totalAuditsCompleted;

    event ShareAssigned(address indexed holder, uint256 amount);
    event AuditRecorded(bytes32 indexed sampleHash, string analysisType, uint256 feePaid, uint256 timestamp);
    event RevenueDistributed(uint256 totalAmount, uint256 timestamp);

    modifier onlyOwner() {
        require(msg.sender == owner, "Restricted access: owner only");
        _;
    }

    constructor(string memory _name, string memory _location, uint256 _totalShares) {
        nodeName = _name;
        nodeLocation = _location;
        owner = msg.sender;
        totalShares = _totalShares;
        shares[msg.sender] = _totalShares;
        shareholders.push(msg.sender);
    }

    /**
     * @notice Allocates shares/equity of the node to an investor.
     */
    function assignShares(address _investor, uint256 _amount) external onlyOwner {
        require(shares[owner] >= _amount, "Insufficient owner shares balance");
        if (shares[_investor] == 0) {
            shareholders.push(_investor);
        }
        shares[owner] -= _amount;
        shares[_investor] += _amount;
        emit ShareAssigned(_investor, _amount);
    }

    /**
     * @notice Records an audit performed by the microscope and deposits the fee into the contract.
     * @param _sampleHash Unique hash of the FE-SEM raw data/image
     * @param _analysisType Analysis category (GSR, Oil&Gas, Environment, Semiconductors)
     */
    function recordAudit(bytes32 _sampleHash, string calldata _analysisType) external payable {
        require(msg.value > 0, "Audit fee must be greater than 0");

        auditHistory.push(AuditRecord({
            sampleHash: _sampleHash,
            analysisType: _analysisType,
            timestamp: block.timestamp,
            feePaid: msg.value
        }));

        totalAuditsCompleted++;
        emit AuditRecorded(_sampleHash, _analysisType, msg.value, block.timestamp);
    }

    /**
     * @notice Automatically distributes accumulated revenues to shareholders proportional to their shares.
     */
    function distributeRevenue() external {
        uint256 balance = address(this).balance;
        require(balance > 0, "No funds available for distribution");

        for (uint256 i = 0; i < shareholders.length; i++) {
            address holder = shareholders[i];
            uint256 holderShare = shares[holder];
            if (holderShare > 0) {
                uint256 payout = (balance * holderShare) / totalShares;
                if (payout > 0) {
                    payable(holder).transfer(payout);
                }
            }
        }

        emit RevenueDistributed(balance, block.timestamp);
    }

    /**
     * @notice Fallback receive function to accept direct funds (e.g., commercial service payments)
     */
    receive() external payable {}
}
