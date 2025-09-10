```mermaid
    flowchart TB
        A[Home Page]
        B[Sign Up]
        C[Sign In]
        D[Contact Form]
        A --> B
        A --> C
        A --> D
        C --> UD

        subgraph sg4[User Profile]
            UD[User Dashboard]
            E[Sign Out]
            EP[Edit Profile]
            CP[Change Password]
            UD --> E
            UD --> EP
            UD --> CP
        end
            
        UD --> BS
        UD --> BD

        subgraph sg1[Accessibility Verification]
            F5[Request Accessibility 
            Verification]
            G4[Accessibility Verification
            Report Form]
            G6[Accessibility
            Verification Report]
            WA[Apply to Verify 
                Business Accessibility]
            AS[Application Submitted]
            G2[Accessibility Verification 
            History]
            G5[Cancel Accessibility 
            Verification Application]
            SPBL[Single Page Business Listing:
            Information for Wheelers 
            Verifying Accessibility]
            WA --> AS
            AS --> SPBL
            UD --> G2
            UD --> G4
            UD --> G5
            UD --> SPBL
            G2 --> G6
        end

        subgraph sg2[Business Owners]
            RB[Register Business]
            BD[Business Owner Dashboard]
            F1[Delete Business Profile]
            F2[Edit Business Profile]
            F3[Upgrade Membership]
            F4[View Membership Details]
            UD --> RB
            RB --> BD
            BD --> G6
            BD --> F1
            BD --> F2
            BD --> F3
            BD --> F4
            BD --> F5
            F4 --> F3
        end

        %% Business Search
        subgraph Accessible Business Search
            BS[Business Search & Map]
            BL[Business Listing]
            BS --> BL
            BL --> WA
        end

        subgraph sg3[Checkout Process]
            P1[Enter Payment Details]
            P2[Confirm Purchase]
            P3[Stripe Payment Processing]
            P4[Payment Confirmation Page]
            F5 --> P1
            F3 --> P1
            P1 --> P2
            P2 --> P3
            P3 --> P4
        end

    %% Wheeler-only process (light blue)
    style sg1 fill:#ADD8E6,stroke:#333,stroke-width:1px

    %% Business Owner-only process (sage green)
    style sg2 fill:#E0E4DBCC,stroke:#333,stroke-width:1px
    style sg3 fill:#E0E4DBCC,stroke:#333,stroke-width:1px
```