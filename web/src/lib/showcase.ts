import chair from '@/assets/showcase/m-nilambur-teak-dining-chair.webp'
import sofa from '@/assets/showcase/m-three-seater-sofa-mustard-yellow.webp'
import tee from '@/assets/showcase/m-classic-crew-neck-t-shirt-red.webp'
import teapot from '@/assets/showcase/m-th-i-re-bleu.webp'
import { PAPERS, type Paper } from './paper'

/** Photos Pictalog made from the sample files, with the row each one came from. */
export const SHOWCASE: { src: string; row: string[]; paper: Paper }[] = [
  { src: teapot, row: ['Théière', 'Bleu', '32,00 €'], paper: 'pearl' },
  { src: chair, row: ['Nilambur teak dining chair', '₹6,500'], paper: 'silver' },
  { src: sofa, row: ['3-seater sofa', 'mustard yellow', '₹62,000'], paper: 'ash' },
  { src: tee, row: ['Crew neck tee', 'Red', '₹499'], paper: 'chalk' },
]

/** Every sample photo, each on its own backdrop: the wall of products on the sign-in page. */
export const GALLERY: { src: string; paper: Paper }[] = Object.values(
  import.meta.glob<string>('@/assets/showcase/m-*.webp', { eager: true, import: 'default' }),
).map((src, i) => ({ src, paper: PAPERS[i % PAPERS.length] }))
