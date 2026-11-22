-- =============================================================================
-- Real Estate RFM Lead Segmentation (SQL)
-- =============================================================================
-- Πώς προσαρμόζουμε τη λογική RFM σε κλάδο χωρίς επαναλαμβανόμενες αγορές:
--   * Recency (R)   : Ημέρες από την τελευταία ΕΙΣΕΡΧΟΜΕΝΗ κίνηση πελάτη
--                     (αγνοούμε τα δικά μας outbound follow-ups!).
--   * Frequency (F) : Πλήθος εισερχόμενων σημάτων (αιτήματα, κλήσεις, μηνύματα)
--                     + αν έχει πραγματοποιήσει επίσκεψη (υπόδειξη ακινήτου).
--   * Monetary (M)  : Δηλωμένο budget του πελάτη (επιταχυντής από 200.000€+).
-- =============================================================================

-- Βήμα 1: Κρατάμε ΜΟΝΟ τις εισερχόμενες επικοινωνίες του πελάτη (inbound)
WITH inbound_activity AS (
    SELECT
        lead_id,
        MAX(event_date)                                             AS last_inbound_date,
        COUNT(*)                                                    AS signals_count,
        MAX(CASE WHEN event_type = 'property_visit' THEN 1 ELSE 0 END) AS has_visit
    FROM sample_interactions
    WHERE direction = 'inbound'   -- Κρίσιμο: δεν μετράμε τις δικές μας κλήσεις/emails!
    GROUP BY lead_id
),

-- Βήμα 2: Συνδυασμός με τα στοιχεία του πελάτη & υπολογισμός Recency σε ημέρες
lead_metrics AS (
    SELECT
        l.lead_id,
        l.full_name,
        l.email,
        l.area,
        l.property_type,
        l.budget,
        COALESCE(a.signals_count, 0)                                AS signals_count,
        COALESCE(a.has_visit, 0)                                    AS has_visit,
        a.last_inbound_date,
        -- Σημείωση: Σε PostgreSQL: (CURRENT_DATE - a.last_inbound_date)
        -- Σε SQLite: CAST(julianday('2026-11-22') - julianday(a.last_inbound_date) AS INT)
        CAST(julianday('2026-11-22') - julianday(a.last_inbound_date) AS INTEGER)
                                                                    AS days_since_inbound
    FROM sample_crm_leads AS l
    LEFT JOIN inbound_activity AS a
        ON l.lead_id = a.lead_id
),

-- Βήμα 3: Εφαρμογή των 5 κανόνων Segmentation (Lifecycle State Machine)
segmented_leads AS (
    SELECT
        *,
        CASE
            WHEN days_since_inbound <= 60
                 AND (
                     has_visit = 1
                     OR signals_count >= 4
                     OR (signals_count BETWEEN 2 AND 3 AND budget >= 200000)
                 )
                THEN 'Έτοιμος αγοραστής'

            WHEN days_since_inbound <= 60
                THEN 'Νέος ενδιαφερόμενος'

            WHEN days_since_inbound BETWEEN 61 AND 180
                THEN 'Σε σκέψη'

            WHEN days_since_inbound BETWEEN 181 AND 365
                THEN 'Σε ψύξη'

            ELSE 'Σε νάρκη'
        END AS segment,

        -- Προαιρετικό Alert: Εντοπίζει «Έτοιμους» που πλησιάζουν το όριο των 60 ημερών
        CASE
            WHEN days_since_inbound BETWEEN 45 AND 60
                 AND (
                     has_visit = 1
                     OR signals_count >= 4
                     OR (signals_count BETWEEN 2 AND 3 AND budget >= 200000)
                 )
                THEN 1
            ELSE 0
        END AS at_risk_60d_alert
    FROM lead_metrics
)

-- Βήμα 4: Τελική λίστα για export σε Email Campaigns
SELECT
    lead_id,
    full_name,
    email,
    area,
    budget,
    signals_count,
    has_visit,
    days_since_inbound,
    segment,
    at_risk_60d_alert
FROM segmented_leads
ORDER BY
    CASE segment
        WHEN 'Έτοιμος αγοραστής'   THEN 1
        WHEN 'Νέος ενδιαφερόμενος' THEN 2
        WHEN 'Σε σκέψη'            THEN 3
        WHEN 'Σε ψύξη'             THEN 4
        ELSE 5
    END,
    days_since_inbound ASC;


-- =============================================================================
-- Bonus Query: Σύνοψη KPIs ανά Segment (για αναφορά στη διοίκηση / ομάδα)
-- =============================================================================
/*
SELECT
    segment,
    COUNT(*)                                AS leads_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_total,
    SUM(budget)                             AS total_pipeline_budget,
    ROUND(AVG(budget), 0)                   AS avg_budget,
    SUM(at_risk_60d_alert)                  AS at_risk_count
FROM segmented_leads
GROUP BY segment;
*/
