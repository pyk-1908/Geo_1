import { get } from "../utils/requests";

/**
 * Fetch the Salesforce notes for an Account. Returns the raw response so the
 * caller can distinguish notes vs. empty vs. auth failure vs. error:
 *   success: { account_id, notes: [...] }
 *   401:     { success: false, unauthorized: true }
 *   error:   { success: false, message }
 */
export async function getAccountNotes(accountId: string) {
    return await get(`/salesforce/notes/?account_id=${encodeURIComponent(accountId)}`);
}
